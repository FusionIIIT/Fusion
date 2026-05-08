param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$ApiPrefix = ""   # set to "/api/hr" only if your project mounts these urls under that prefix
)

$ErrorActionPreference = "Stop"

# Update these if your evaluator uses different credentials
$RoleUsers = @{
    "employee"   = @{ username = "rahul1001";     password = "rahul123" }
    "hod"        = @{ username = "hod1002";       password = "hod123" }
    "director"   = @{ username = "director1003";   password = "director123" }
    "registrar"  = @{ username = "registrar1004";  password = "registrar123" }
    "hradmin"    = @{ username = "hradmin1005";    password = "hradmin123" }
    "accountant" = @{ username = "accountant1006"; password = "accountant123" }
}

function Join-ApiUrl {
    param(
        [string]$Base,
        [string]$Prefix,
        [string]$Path
    )

    $base = $Base.TrimEnd('/')
    $prefix = $Prefix.Trim('/')
    $path = $Path.TrimStart('/')

    if ([string]::IsNullOrWhiteSpace($prefix)) {
        return "$base/$path"
    }

    return "$base/$prefix/$path"
}

function Resolve-Token {
    param([object]$Response)

    if ($null -eq $Response) { return $null }
    if ($Response.token) { return $Response.token }
    if ($Response.key) { return $Response.key }
    if ($Response.auth_token) { return $Response.auth_token }
    if ($Response.data -and $Response.data.token) { return $Response.data.token }
    return $null
}

function Login-Role {
    param([string]$Role)

    if (-not $RoleUsers.ContainsKey($Role)) {
        throw "Unknown role '$Role'. Available roles: $($RoleUsers.Keys -join ', ')"
    }

    $creds = $RoleUsers[$Role]
    $uri = Join-ApiUrl -Base $BaseUrl -Prefix $ApiPrefix -Path "/api/auth/login/"
    $body = @{ username = $creds.username; password = $creds.password } | ConvertTo-Json

    try {
        $resp = Invoke-RestMethod -Method Post -Uri $uri -ContentType "application/json" -Body $body
        $token = Resolve-Token -Response $resp

        if (-not $token) {
            throw "Login succeeded but no token field was found in the response."
        }

        return [pscustomobject]@{
            role     = $Role
            username = $creds.username
            token    = $token
        }
    }
    catch {
        throw "Login failed for role '$Role' (user: $($creds.username)): $($_.Exception.Message)"
    }
}

function Invoke-ApiAsRole {
    param(
        [Parameter(Mandatory = $true)][string]$Role,
        [Parameter(Mandatory = $true)][string]$Path,
        [ValidateSet("GET", "POST", "PUT", "PATCH", "DELETE")][string]$Method = "GET",
        [hashtable]$Body = $null
    )

    $session = Login-Role -Role $Role
    $uri = Join-ApiUrl -Base $BaseUrl -Prefix $ApiPrefix -Path $Path
    $headers = @{
        Authorization = "Token $($session.token)"
        Accept        = "application/json"
    }

    try {
        $params = @{
            Method             = $Method
            Uri                = $uri
            Headers            = $headers
            ErrorAction        = "Stop"
            MaximumRedirection = 0   # important: lets you see 301 instead of silently following it
        }

        if ($Body) {
            $params.ContentType = "application/json"
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
        }

        $resp = Invoke-WebRequest @params

        $content = $resp.Content
        $parsed = $content
        try {
            if ($content) {
                $parsed = $content | ConvertFrom-Json
            }
        } catch {
            $parsed = $content
        }

        return [pscustomobject]@{
            role     = $Role
            method   = $Method
            path     = $Path
            uri      = $uri
            status   = [int]$resp.StatusCode
            ok       = $true
            response = $parsed
        }
    }
    catch {
        $status = 0
        $raw = ""

        if ($_.Exception.Response) {
            try {
                $status = [int]$_.Exception.Response.StatusCode
                $stream = $_.Exception.Response.GetResponseStream()
                if ($stream) {
                    $reader = New-Object System.IO.StreamReader($stream)
                    $raw = $reader.ReadToEnd()
                    $reader.Close()
                }
            } catch {
                $raw = $_.Exception.Message
            }
        } else {
            $raw = $_.Exception.Message
        }

        return [pscustomobject]@{
            role     = $Role
            method   = $Method
            path     = $Path
            uri      = $uri
            status   = $status
            ok       = $false
            response = $raw
        }
    }
}

function Test-RbacCase {
    param(
        [Parameter(Mandatory = $true)][string]$ActorRole,
        [Parameter(Mandatory = $true)][string]$Path,
        [ValidateSet("GET", "POST", "PUT", "PATCH", "DELETE")][string]$Method = "GET",
        [int[]]$ExpectedUnauthorizedCodes = @(401, 403, 301),
        [hashtable]$Body = $null
    )

    $result = Invoke-ApiAsRole -Role $ActorRole -Path $Path -Method $Method -Body $Body
    $pass = $ExpectedUnauthorizedCodes -contains $result.status

    [pscustomobject]@{
        actor               = $ActorRole
        method              = $Method
        path                = $Path
        observedStatus      = $result.status
        expectedUnauthorized = ($ExpectedUnauthorizedCodes -join ",")
        pass                = $pass
        response            = $result.response
    }
}

# Representative endpoints from your hr_api urls
$RbacCases = @(
    @{ Name = "employees-list";              Path = "/employees/";                                   Method = "GET"  },
    @{ Name = "employees-detail";            Path = "/employees/1/";                                 Method = "GET"  },

    @{ Name = "leave-list-create";           Path = "/leave-applications/";                          Method = "GET"  },
    @{ Name = "leave-detail";                Path = "/leave-applications/1/";                        Method = "GET"  },
    @{ Name = "leave-balance";               Path = "/leave-balance/";                               Method = "GET"  },
    @{ Name = "leave-balance-other";         Path = "/leave-balance/1/";                             Method = "GET"  },
    @{ Name = "leave-responsibility";        Path = "/leave-applications/1/responsibility/reviewer/"; Method = "POST" },
    @{ Name = "leave-request-document";      Path = "/leave-applications/1/request-document/";       Method = "POST" },
    @{ Name = "leave-submit-document";       Path = "/leave-applications/1/submit-document/";       Method = "POST" },
    @{ Name = "leave-download";              Path = "/leave-applications/1/download/";               Method = "GET"  },
    @{ Name = "leave-withdraw";              Path = "/leave-applications/1/withdraw/";               Method = "POST" },
    @{ Name = "leave-cancel-request";        Path = "/leave-applications/1/cancel-request/";         Method = "POST" },
    @{ Name = "leave-cancel-decision";       Path = "/leave-applications/1/cancel-decision/approve/"; Method = "POST" },
    @{ Name = "leave-extension-request";     Path = "/leave-applications/1/extension-request/";      Method = "POST" },
    @{ Name = "leave-extension-decision";    Path = "/leave-applications/1/extension-decision/approve/"; Method = "POST" },
    @{ Name = "leave-resumption";            Path = "/leave-applications/1/resumption/";             Method = "POST" },
    @{ Name = "leave-resumption-decision";   Path = "/leave-applications/1/resumption-decision/approve/"; Method = "POST" },
    @{ Name = "leave-decision";              Path = "/leave-applications/1/approve/";                Method = "POST" },
    @{ Name = "leave-nominee-dashboard";     Path = "/leave-nominee/";                               Method = "GET"  },
    @{ Name = "leave-nominee-decision";      Path = "/leave-nominee/1/";                             Method = "POST" },

    @{ Name = "attendance";                  Path = "/attendance/";                                  Method = "GET"  },

    @{ Name = "appraisal-periods";           Path = "/appraisal-periods/";                           Method = "GET"  },
    @{ Name = "appraisals";                  Path = "/appraisals/";                                  Method = "GET"  },

    @{ Name = "training-programs";           Path = "/training-programs/";                           Method = "GET"  },
    @{ Name = "training-nominations";        Path = "/training-nominations/";                        Method = "POST" },

    @{ Name = "promotions";                  Path = "/promotions/";                                  Method = "POST" },

    @{ Name = "workload";                    Path = "/workload/";                                    Method = "GET"  },

    @{ Name = "ltc-list-create";             Path = "/ltc/";                                         Method = "GET"  },
    @{ Name = "ltc-detail";                  Path = "/ltc/1/";                                       Method = "GET"  },
    @{ Name = "ltc-download";                Path = "/ltc/1/download/";                              Method = "GET"  },
    @{ Name = "ltc-withdraw";                Path = "/ltc/1/withdraw/";                              Method = "POST" },
    @{ Name = "ltc-decision";                Path = "/ltc/1/approve/";                                Method = "POST" },

    @{ Name = "cpda-advance-list";           Path = "/cpda-advances/";                               Method = "GET"  },
    @{ Name = "cpda-advance-detail";         Path = "/cpda-advances/1/";                             Method = "GET"  },
    @{ Name = "cpda-advance-download";       Path = "/cpda-advances/1/download/";                    Method = "GET"  },
    @{ Name = "cpda-advance-withdraw";       Path = "/cpda-advances/1/withdraw/";                    Method = "POST" },
    @{ Name = "cpda-advance-decision";       Path = "/cpda-advances/1/approve/";                     Method = "POST" },

    @{ Name = "cpda-reimbursement-list";     Path = "/cpda-reimbursements/";                         Method = "GET"  },
    @{ Name = "cpda-reimbursement-detail";   Path = "/cpda-reimbursements/1/";                       Method = "GET"  },
    @{ Name = "cpda-reimbursement-decision"; Path = "/cpda-reimbursements/1/approve/";               Method = "POST" },

    @{ Name = "appraisal-form-list";         Path = "/appraisal-forms/";                             Method = "GET"  },
    @{ Name = "appraisal-form-detail";       Path = "/appraisal-forms/1/";                           Method = "GET"  },
    @{ Name = "appraisal-form-download";     Path = "/appraisal-forms/1/download/";                  Method = "GET"  },
    @{ Name = "appraisal-form-review";       Path = "/appraisal-forms/1/review/";                    Method = "POST" },
    @{ Name = "appraisal-form-assign";       Path = "/appraisal-forms/1/assign/";                    Method = "POST" }
)

function Invoke-RbacSweep {
    param(
        [string[]]$Roles = @("employee", "hod", "director", "registrar", "hradmin", "accountant")
    )

    $results = foreach ($case in $RbacCases) {
        foreach ($role in $Roles) {
            Test-RbacCase -ActorRole $role -Path $case.Path -Method $case.Method
        }
    }

    $results | Select-Object actor, method, path, observedStatus, expectedUnauthorized, pass |
        Format-Table -AutoSize
}

function Show-RbacMatrix {
    param([string]$Path)

    $roles = @("employee", "hod", "director", "registrar", "hradmin", "accountant")
    $rows = foreach ($role in $roles) {
        Invoke-ApiAsRole -Role $role -Path $Path -Method "GET"
    }

    $rows | Select-Object role, method, path, status, ok | Format-Table -AutoSize
}

Write-Host "Loaded RBAC evaluator for $BaseUrl" -ForegroundColor Green
Write-Host "Functions: Login-Role, Invoke-ApiAsRole, Test-RbacCase, Show-RbacMatrix, Invoke-RbacSweep" -ForegroundColor Cyan