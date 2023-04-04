// go run script.go -dir ~/branches -b "ac-2 os-2" -og ~/branches/main -rem origin
// go run script.go -dir ~/branches -b "ac-2 os-2" -og ~/branches/main -rem origin -db ~/fusiondb_07feb23.sql

package main

import (
	"bytes"
	"flag"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
	"syscall"
)

type Ports struct {
	App int
	Db  int
}

var (
	dirPath     = flag.String("dir", "~", "path of directory in which all branches are present")
	branchNames = flag.String("b", "", "branches which needs to be synced")
	ogPath      = flag.String("og", "", "path of directory to be copied")
	remoteName  = flag.String("rem", "origin", "git remote name where branch is present")
	db_dumpPath = flag.String("db", "", "path of dump file that is to be imported")
)

var branchPorts = map[string]Ports{
	"test":  {App: 8000, Db: 5431},
	"ac":    {App: 8019, Db: 5450},
	"ac-1":  {App: 8001, Db: 5451},
	"ac-2":  {App: 8002, Db: 5452},
	"ac-3":  {App: 8003, Db: 5453},
	"ac-4":  {App: 8004, Db: 5454},
	"ac-5":  {App: 8005, Db: 5455},
	"gad-1": {App: 8006, Db: 5456},
	"gad-2": {App: 8007, Db: 5457},
	"gad-3": {App: 8008, Db: 5458},
	"gad-4": {App: 8009, Db: 5459},
	"gad-5": {App: 8010, Db: 5460},
	"os-1":  {App: 8011, Db: 5461},
	"os-2":  {App: 8012, Db: 5462},
	"os-3":  {App: 8013, Db: 5463},
	"os-4":  {App: 8014, Db: 5464},
	"sa-1":  {App: 8015, Db: 5465},
	"sa-2":  {App: 8016, Db: 5466},
	"sa-3":  {App: 8017, Db: 5467},
	"sa-4":  {App: 8018, Db: 5468},
	"hr":    {App: 8020, Db: 5469},
	"rspc":  {App: 8021, Db: 5470},
	"ps-1":  {App: 8022, Db: 5471},
	"ps-2":  {App: 8023, Db: 5472},
}

func main() {
	flag.Parse()
	log.SetFlags(log.Lshortfile)

	if _, err := os.Stat(*ogPath); os.IsNotExist(err) {
		log.Fatal("path of main directory not provided")
	}
	if len(*branchNames) == 0 {
		log.Fatal("no branch provided")
	}

	branches := strings.Split((*branchNames), " ")
	for _, branch := range branches {
		branchDir := filepath.Join(*dirPath, branch)

		// If branch directory does not exists, we will make a copy from the reference directory
		// NOTE: we are not cloning from github because it will take a long time
		if _, err := os.Stat(branchDir); os.IsNotExist(err) {
			fmt.Println("Cloning ", branchDir)
			err := CopyDirectory(*ogPath, branchDir)
			if err != nil {
				log.Fatal(err)
			}
		}

		fmt.Printf("Fetching branch %s from %s...\n", branch, *remoteName)
		cmdRun(fmt.Sprintf("git -C %s fetch %s %s", branchDir, *remoteName, branch), true)
		cmdRun(fmt.Sprintf("git -C %s restore %s", branchDir, branchDir), true)

		// If the does not branch exists, then we switch to that branch
		// otherwise we will just merge the changes
		if !strings.Contains(cmdRun(fmt.Sprintf("git -C %s branch --show-current", branchDir), false), branch) {
			fmt.Println(branch, "branch not found, pulling from", *remoteName, "...")
			cmdRun(fmt.Sprintf("git -C %s switch -c %s %s/%s", branchDir, branch, *remoteName, branch), true)
		} else {
			fmt.Printf("Merging %s/%s to %s\n", *remoteName, branch, *remoteName)
			cmdRun(fmt.Sprintf("git -C %s merge %s/%s", branchDir, *remoteName, branch), true)
			cmdRun(fmt.Sprintf("docker-compose -f %s down || true", filepath.Join(branchDir, "docker-compose.yml")), true)
		}

		fmt.Printf("Making necessary changes... \n")
		ReplaceAllInFile(
			filepath.Join(branchDir, "docker-compose.yml"),
			`5432:`,
			fmt.Sprintf("%d:", branchPorts[branch].Db))
		ReplaceAllInFile(
			filepath.Join(branchDir, "docker-compose.yml"),
			`8000:`,
			fmt.Sprintf("%d:", branchPorts[branch].App))
		ReplaceAllInFile(
			filepath.Join(branchDir, "docker-compose.yml"),
			`postgresql:`,
			fmt.Sprintf("postgresql-%s", branch))

		fmt.Printf("Building %s\n", branch)
		cmdRun(fmt.Sprintf("docker-compose -f %s build", filepath.Join(branchDir, "docker-compose.yml")), true)
		cmdRun(fmt.Sprintf("docker-compose -f %s up -d", filepath.Join(branchDir, "docker-compose.yml")), true)

		if len(*db_dumpPath) > 0 {
			fmt.Printf("Importing dump into %s_db_1\n", branch)
			cmdRun(
				fmt.Sprintf(
					"docker exec -i %s_db_1 psql -U fusion_admin -d fusionlab < %s",
					branch,
					*db_dumpPath,
				),
				true)
		}

		cmdRun(
			fmt.Sprintf(
				"docker exec -i %s_app_1 python FusionIIIT/manage.py migrate",
				branch,
			),
			true)

		fmt.Printf("%s app started at port %d\n", branch, branchPorts[branch].App)
	}
}

func cmdRun(command string, shouldPrint bool) string {
	var stdout bytes.Buffer
	var stderr bytes.Buffer
	cmd := exec.Command("bash", "-c", command)
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	err := cmd.Run()
	if err != nil {
		log.Fatal(command, " failed!\n ", err)
	}
	outerr := stderr.String()
	out := stdout.String()
	if shouldPrint {
		fmt.Println(outerr, out)
	}
	return out
}

func ReplaceAllInFile(fileP, pattern, finalString string) error {
	input, err := ioutil.ReadFile(fileP)
	if err != nil {
		log.Fatal(err)
	}

	lines := strings.Split(string(input), "\n")

	re := regexp.MustCompile(pattern)

	for i, line := range lines {
		lines[i] = re.ReplaceAllString(line, finalString)
	}
	output := strings.Join(lines, "\n")
	err = ioutil.WriteFile(fileP, []byte(output), 0644)
	if err != nil {
		log.Fatal(err)
	}
	return nil
}

func CopyDirectory(scrDir, dest string) error {
	entries, err := os.ReadDir(scrDir)
	if err != nil {
		return err
	}
	for _, entry := range entries {
		if entry.Name() == "env" {
			continue
		}
		sourcePath := filepath.Join(scrDir, entry.Name())
		destPath := filepath.Join(dest, entry.Name())

		fileInfo, err := os.Stat(sourcePath)
		if err != nil {
			return err
		}

		stat, ok := fileInfo.Sys().(*syscall.Stat_t)
		if !ok {
			return fmt.Errorf("failed to get raw syscall.Stat_t data for '%s'", sourcePath)
		}

		switch fileInfo.Mode() & os.ModeType {
		case os.ModeDir:
			if err := CreateIfNotExists(destPath, 0755); err != nil {
				return err
			}
			if err := CopyDirectory(sourcePath, destPath); err != nil {
				return err
			}
		case os.ModeSymlink:
			if err := CopySymLink(sourcePath, destPath); err != nil {
				return err
			}
		default:
			if err := Copy(sourcePath, destPath); err != nil {
				return err
			}
		}

		if err := os.Lchown(destPath, int(stat.Uid), int(stat.Gid)); err != nil {
			return err
		}

		fInfo, err := entry.Info()
		if err != nil {
			return err
		}

		isSymlink := fInfo.Mode()&os.ModeSymlink != 0
		if !isSymlink {
			if err := os.Chmod(destPath, fInfo.Mode()); err != nil {
				return err
			}
		}
	}
	return nil
}

func Copy(srcFile, dstFile string) error {
	out, err := os.Create(dstFile)
	if err != nil {
		return err
	}

	defer out.Close()

	in, err := os.Open(srcFile)
	defer in.Close()
	if err != nil {
		return err
	}

	_, err = io.Copy(out, in)
	if err != nil {
		return err
	}

	return nil
}

func Exists(filePath string) bool {
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		return false
	}

	return true
}

func CreateIfNotExists(dir string, perm os.FileMode) error {
	if Exists(dir) {
		return nil
	}

	if err := os.MkdirAll(dir, perm); err != nil {
		return fmt.Errorf("failed to create directory: '%s', error: '%s'", dir, err.Error())
	}

	return nil
}

func CopySymLink(source, dest string) error {
	link, err := os.Readlink(source)
	if err != nil {
		return err
	}
	return os.Symlink(link, dest)
}
