"""
Awards API — Views (Raw SQL approach)
awardsScholarships/api/views_awards.py

Uses raw SQL to avoid Django ORM model registration conflicts with
the existing awardsScholarships app models.

All award tables are created via create_awards_tables.py.
"""
import csv
import io
import json
from django.http import HttpResponse
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# ── Grade → Points mapping ────────────────────────────────────────────────────
GRADE_POINTS = {
    'O': 10, 'A+': 9, 'A': 8, 'B+': 7, 'B': 6,
    'C+': 5, 'C': 4, 'D+': 3, 'D': 2, 'F': 0,
}
UG_PROGRAMMES = ('B.Tech', 'B.Des')
PG_PROGRAMMES = ('M.Tech', 'M.Des', 'PhD')

AWARD_TYPE_LABELS = {
    'IIITDM_PRIZE':    'IIITDM Proficiency Prize',
    'CULTURAL':        'Cultural Medal',
    'SPORTS':          'Sports Medal',
    'DM_PROFICIENCY':  'D&M Proficiency Gold Medal',
    'DIRECTOR_SILVER': "Director's Silver Medal",
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def calculate_cpi_for_roll(roll_no):
    """Dynamically calculate CPI from online_cms_student_grades + programme_curriculum_course."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT g.grade, c.credit
            FROM online_cms_student_grades g
            JOIN programme_curriculum_course c ON c.id = g.course_id_id
            WHERE UPPER(g.roll_no) = UPPER(%s)
        """, [roll_no])
        rows = cur.fetchall()

    if not rows:
        return 0.0
    total_credits, weighted_sum = 0, 0.0
    for grade, credit in rows:
        pts = GRADE_POINTS.get(str(grade).strip(), 0)
        credit = credit or 0
        weighted_sum += pts * credit
        total_credits += credit
    return round(weighted_sum / total_credits, 2) if total_credits else 0.0


def get_student_row(request):
    """Return a dict with student + extra_info fields for the current user, or None."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                ei.id          AS roll_no,
                au.first_name,
                au.last_name,
                au.email,
                s.programme,
                s.batch,
                s.category,
                di.name        AS branch
            FROM globals_extrainfo ei
            JOIN auth_user au ON au.id = ei.user_id
            JOIN academic_information_student s ON s.id_id = ei.id
            LEFT JOIN globals_departmentinfo di ON di.id = ei.department_id
            WHERE au.id = %s
        """, [request.user.id])
        row = cur.fetchone()
    if not row:
        return None
    cols = ['roll_no','first_name','last_name','email','programme','batch','category','branch']
    d = dict(zip(cols, row))
    d['name'] = f"{d.pop('first_name')} {d.pop('last_name')}".strip() or request.user.username
    return d


# =============================================================================
# STUDENT VIEWS
# =============================================================================

class AwardsStudentProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student = get_student_row(request)
        if not student:
            return Response({'error': 'Student profile not found.'}, status=404)
        student['cpi'] = calculate_cpi_for_roll(student['roll_no'])
        return Response(student)


class AutoAwardsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        with connection.cursor() as cur:
            cur.execute("""
                SELECT
                    r.id, r.award_name, r.award_code,
                    ei.id AS roll_no,
                    au.first_name || ' ' || au.last_name AS student_name,
                    r.programme, r.branch, r.batch, r.cpi,
                    TO_CHAR(r.generated_at, 'YYYY-MM-DD HH24:MI') AS generated_at
                FROM awards_auto_award_result r
                JOIN globals_extrainfo ei ON ei.id = r.student_id
                JOIN auth_user au ON au.id = ei.user_id
                ORDER BY r.award_name, r.cpi DESC
            """)
            cols = [c.name for c in cur.description]
            rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        return Response(rows)


class StudentAwardApplicationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student = get_student_row(request)
        if not student:
            return Response([])
        with connection.cursor() as cur:
            cur.execute("""
                SELECT id, award_type, form_data,
                       TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') AS created_at
                FROM awards_award_application
                WHERE student_id = %s
                ORDER BY created_at DESC
            """, [student['roll_no']])
            cols = [c.name for c in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        for r in rows:
            r['award_label'] = AWARD_TYPE_LABELS.get(r['award_type'], r['award_type'])
        return Response(rows)


class AwardApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        student = get_student_row(request)
        if not student:
            return Response({'error': 'Student profile not found.'}, status=404)

        award_type = str(request.data.get('award_type', '')).upper()
        if award_type not in AWARD_TYPE_LABELS:
            return Response({'error': f'Invalid award_type. Choose from: {list(AWARD_TYPE_LABELS)}'}, status=400)

        form_data = request.data.get('form_data', {})
        if isinstance(form_data, str):
            try:
                form_data = json.loads(form_data)
            except Exception:
                return Response({'error': 'form_data must be JSON.'}, status=400)

        cpi = calculate_cpi_for_roll(student['roll_no'])
        form_data.update({
            'roll_no':   student['roll_no'],
            'name':      student['name'],
            'programme': student['programme'],
            'batch':     student['batch'],
            'cpi':       cpi,
            'branch':    student['branch'],
        })

        form_data_json = json.dumps(form_data)
        with connection.cursor() as cur:
            cur.execute("SELECT id FROM awards_award_application WHERE student_id=%s AND award_type=%s",
                        [student['roll_no'], award_type])
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    "UPDATE awards_award_application SET form_data=%s, updated_at=NOW() WHERE id=%s",
                    [form_data_json, existing[0]]
                )
                return Response({'id': existing[0], 'created': False,
                                 'award_type': award_type,
                                 'award_label': AWARD_TYPE_LABELS[award_type],
                                 'message': 'Application updated successfully.'})
            else:
                cur.execute(
                    """INSERT INTO awards_award_application (student_id, award_type, form_data, created_at, updated_at)
                       VALUES (%s, %s, %s, NOW(), NOW()) RETURNING id""",
                    [student['roll_no'], award_type, form_data_json]
                )
                new_id = cur.fetchone()[0]
                return Response({'id': new_id, 'created': True,
                                 'award_type': award_type,
                                 'award_label': AWARD_TYPE_LABELS[award_type],
                                 'message': 'Application submitted successfully.'}, status=201)


# =============================================================================
# ASSISTANT VIEWS
# =============================================================================

class GenerateAutoAwardsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        batch = int(request.data.get('batch', 2023))

        # Fetch all students in batch with their dept
        with connection.cursor() as cur:
            cur.execute("""
                SELECT
                    ei.id AS roll_no,
                    au.first_name || ' ' || au.last_name AS name,
                    s.programme,
                    COALESCE(di.name, '') AS branch
                FROM academic_information_student s
                JOIN globals_extrainfo ei ON ei.id = s.id_id
                JOIN auth_user au ON au.id = ei.user_id
                LEFT JOIN globals_departmentinfo di ON di.id = ei.department_id
                WHERE s.batch = %s
            """, [batch])
            cols = [c.name for c in cur.description]
            students = [dict(zip(cols, r)) for r in cur.fetchall()]

        if not students:
            return Response({'error': f'No students for batch {batch}.'}, status=404)

        # Compute CPI for each student
        for s in students:
            s['cpi'] = calculate_cpi_for_roll(s['roll_no'])

        # Clear old results for this batch
        with connection.cursor() as cur:
            cur.execute("DELETE FROM awards_auto_award_result WHERE batch=%s", [batch])

        generated = []

        def insert_award(award_name, award_code, s):
            with connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO awards_auto_award_result
                        (award_name, award_code, student_id, cpi, programme, branch, batch, generated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                """, [award_name, award_code, s['roll_no'], s['cpi'], s['programme'], s['branch'], batch])
            generated.append({'award': award_name, 'student': s['name'], 'cpi': s['cpi']})

        # CGM — highest overall
        # Only consider students with CPI > 0
        valid_students = [s for s in students if s['cpi'] > 0]
        if valid_students:
            max_cpi = max(s['cpi'] for s in valid_students)
            # Pick ONLY ONE for Chairman (highest CPI, break ties by roll number)
            cgm_winners = sorted([x for x in valid_students if x['cpi'] == max_cpi], key=lambda x: x['roll_no'])
            if cgm_winners:
                insert_award("Chairman's Gold Medal", 'CGM', cgm_winners[0])

        # DGM — Top B.Tech and Top M.Tech
        for code, label, prog_name in [
            ('DGM_BTECH', "Director's Gold Medal (B.Tech)", 'B.Tech'),
            ('DGM_MTECH', "Director's Gold Medal (M.Tech)", 'M.Tech'),
        ]:
            group = [s for s in valid_students if s['programme'] == prog_name]
            if group:
                cat_max = max(s['cpi'] for s in group)
                # Pick ONE winner (highest CPI, break ties by roll number)
                dgm_winners = sorted([x for x in group if x['cpi'] == cat_max], key=lambda x: x['roll_no'])
                if dgm_winners:
                    insert_award(label, code, dgm_winners[0])

        # Academic Silver — by (programme, branch)
        branch_groups = {}
        for s in valid_students:
            key = (s['programme'], s['branch'])
            branch_groups.setdefault(key, []).append(s)

        for (prog, branch), group in branch_groups.items():
            b_max = max(s['cpi'] for s in group)
            code = f"ASM_{prog}_{branch}".upper().replace(' ', '_')[:30]
            label = f"Academic Silver Medal — {prog}"
            if branch:
                label += f" ({branch})"
            
            # Pick ONE winner for Silver Medal per branch to avoid long lists
            asm_winners = sorted([x for x in group if x['cpi'] == b_max], key=lambda x: x['roll_no'])
            if asm_winners:
                insert_award(label, code, asm_winners[0])

        return Response({
            'batch': batch,
            'generated': len(generated),
            'awards': generated,
            'message': f'Auto awards generated for batch {batch}. {len(generated)} entries created.',
        }, status=201)


class AwardApplicationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        award_type = request.query_params.get('award_type', '').upper()
        params = []
        where = ''
        if award_type:
            where = 'AND a.award_type = %s'
            params.append(award_type)

        with connection.cursor() as cur:
            cur.execute(f"""
                SELECT
                    a.id, a.award_type, a.form_data,
                    ei.id AS roll_no,
                    au.first_name || ' ' || au.last_name AS student_name,
                    s.programme,
                    COALESCE(di.name, '') AS branch,
                    TO_CHAR(a.created_at, 'YYYY-MM-DD HH24:MI') AS created_at
                FROM awards_award_application a
                JOIN globals_extrainfo ei ON ei.id = a.student_id
                JOIN auth_user au ON au.id = ei.user_id
                JOIN academic_information_student s ON s.id_id = ei.id
                LEFT JOIN globals_departmentinfo di ON di.id = ei.department_id
                WHERE 1=1 {where}
                ORDER BY a.created_at DESC
            """, params)
            cols = [c.name for c in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]

        for r in rows:
            r['award_label'] = AWARD_TYPE_LABELS.get(r['award_type'], r['award_type'])
            r['cpi'] = calculate_cpi_for_roll(r['roll_no'])

        return Response(rows)


class AwardApplicationExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        award_type = request.query_params.get('award_type', '').upper()
        params = []
        where = ''
        if award_type:
            where = 'AND a.award_type = %s'
            params.append(award_type)

        with connection.cursor() as cur:
            cur.execute(f"""
                SELECT a.award_type, ei.id AS roll_no,
                    au.first_name || ' ' || au.last_name AS name,
                    s.programme, COALESCE(di.name,'') AS branch,
                    a.form_data, TO_CHAR(a.created_at,'YYYY-MM-DD') AS applied_at
                FROM awards_award_application a
                JOIN globals_extrainfo ei ON ei.id=a.student_id
                JOIN auth_user au ON au.id=ei.user_id
                JOIN academic_information_student s ON s.id_id=ei.id
                LEFT JOIN globals_departmentinfo di ON di.id=ei.department_id
                WHERE 1=1 {where}
                ORDER BY a.award_type, a.created_at
            """, params)
            rows = cur.fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Award', 'Roll No', 'Name', 'Programme', 'Branch', 'CPI', 'Form Summary', 'Applied At'])
        for award_type_val, roll_no, name, prog, branch, form_data, applied_at in rows:
            cpi = calculate_cpi_for_roll(roll_no)
            fd = form_data if isinstance(form_data, dict) else json.loads(form_data or '{}')
            summary = ' | '.join(f"{k}: {v}" for k, v in fd.items()
                                  if k not in ('roll_no','name','programme','batch','cpi','branch') and v)[:300]
            writer.writerow([
                AWARD_TYPE_LABELS.get(award_type_val, award_type_val),
                roll_no, name, prog, branch, cpi, summary, applied_at,
            ])

        resp = HttpResponse(output.getvalue(), content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename="award_applications.csv"'
        return resp


class AutoAwardsExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        batch = request.query_params.get('batch', 2023)
        with connection.cursor() as cur:
            cur.execute("""
                SELECT r.award_name, au.first_name||' '||au.last_name AS student_name,
                    ei.id AS roll_no, r.programme, r.branch, r.cpi, r.batch,
                    TO_CHAR(r.generated_at,'YYYY-MM-DD HH24:MI') AS generated_at
                FROM awards_auto_award_result r
                JOIN globals_extrainfo ei ON ei.id=r.student_id
                JOIN auth_user au ON au.id=ei.user_id
                WHERE r.batch=%s
                ORDER BY r.award_name, r.cpi DESC
            """, [batch])
            rows = cur.fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Award Name', 'Student Name', 'Roll No', 'Programme', 'Branch', 'CPI', 'Batch', 'Generated At'])
        for row in rows:
            writer.writerow(row)

        resp = HttpResponse(output.getvalue(), content_type='text/csv')
        resp['Content-Disposition'] = f'attachment; filename="auto_awards_batch{batch}.csv"'
        return resp
