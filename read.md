---                                                       
  1. 需要什么样的 MCP skill                                 
                                                            
  一个 Android 调试桥接器（ADB Bridge），让我能直接从 Mac   
  上读取手机的运行时日志、文件系统和广播状态，而不是靠你转述
  现象来猜问题。

  当前的根本障碍是：我写的代码在手机上运行，出了问题只能靠白
  屏/无反应来判断，完全看不到 Python 异常、Java
  崩溃、广播是否送达、数据库里有没有写入。有了这个
  MCP，我就能直接"看到"手机内部发生了什么。

  ---
  2. 需要哪些具体工具

  ┌─────────────┬───────────────────────────────────────┐
  │  Tool 名称  │                 作用                  │
  ├─────────────┼───────────────────────────────────────┤
  │             │ 抓取手机实时日志，支持按 tag 过滤（如 │
  │ adb_logcat  │  AutoBookkeepAccSvc、NLService、pytho │
  │             │ n）                                   │
  ├─────────────┼───────────────────────────────────────┤
  │ adb_read_fi │ 读取手机上的文件，主要用于读          │
  │ le          │ /data/data/org.example.autobookkeepin │
  │             │ g/files/crash.txt                     │
  ├─────────────┼───────────────────────────────────────┤
  │ adb_shell   │ 执行任意 adb shell 命令（查数据库、检 │
  │             │ 查广播、查权限状态等）                │
  ├─────────────┼───────────────────────────────────────┤
  │ adb_install │ 安装指定路径的 APK 到手机             │
  │ _apk        │                                       │
  ├─────────────┼───────────────────────────────────────┤
  │ adb_list_de │ 列出当前连接的设备，确认连接状态      │
  │ vices       │                                       │
  └─────────────┴───────────────────────────────────────┘

  ---
  3. Go 实现方案

  // main.go
  package main

  import (
        "bufio"
        "context"
        "encoding/json"
        "fmt"
        "os"
        "os/exec"
        "strings"
        "time"

        "github.com/mark3labs/mcp-go/mcp"
        "github.com/mark3labs/mcp-go/server"
  )

  func runADB(args ...string) (string, error) {
        ctx, cancel := context.WithTimeout(context.Backgroun
  30*time.Second)
        defer cancel()
        cmd := exec.CommandContext(ctx, "adb", args...)
        out, err := cmd.CombinedOutput()
        return string(out), err
  }

  func main() {
        s := server.NewMCPServer("android-adb-bridge", "1.0.

        // --- adb_list_devices ---
        s.AddTool(mcp.NewTool("adb_list_devices",
                mcp.WithDescription("List connected Android
  ADB"),
        ), func(ctx context.Context, req mcp.CallToolRequest
  (*mcp.CallToolResult, error) {
                out, err := runADB("devices", "-l")
                if err != nil {
                        return mcp.NewToolResultText("error:
                }
                return mcp.NewToolResultText(out), nil
        })

        // --- adb_logcat ---
        s.AddTool(mcp.NewTool("adb_logcat",
                mcp.WithDescription("Capture Android logcat
  recent logs (last N lines) filtered by optional tag and
  package."),
                mcp.WithString("tag", mcp.Description("Logca
  e.g. 'AutoBookkeepAccSvc' or 'python'. Empty = no
  filter.")),
                mcp.WithString("package", mcp.Description("A
  name to filter by PID, e.g. 'org.example.autobookkeeping'.
   Empty = no filter.")),
                mcp.WithNumber("lines", mcp.Description("Num
  log lines to return (default 200)")),
        ), func(ctx context.Context, req mcp.CallToolRequest
  (*mcp.CallToolResult, error) {
                tag, _ := req.Params.Arguments["tag"].(strin
                pkg, _ := req.Params.Arguments["package"].(s
                linesF, _ := req.Params.Arguments["lines"].(
                lines := int(linesF)
                if lines <= 0 {
                        lines = 200
                }

                // Get PID for package filter
                pidFilter := ""
                if pkg != "" {
                        pidOut, _ := runADB("shell", "pidof"
                        pid := strings.TrimSpace(pidOut)
                        if pid != "" {
                                pidFilter = pid
                        }
                }

                args := []string{"logcat", "-d", "-t", fmt.S
  lines)}
                if tag != "" {
                        args = append(args, "-s", tag+":V")
                }
                out, err := runADB(args...)
                if err != nil {
                        return mcp.NewToolResultText("error:
                }

                // Filter by PID if we have one
                if pidFilter != "" {
                        var filtered []string
                        for _, line := range strings.Split(o
                                if strings.Contains(line, pi
  strings.HasPrefix(line, "-") {
                                        filtered = append(fi
                                }
                        }
                        out = strings.Join(filtered, "\n")
                }

                return mcp.NewToolResultText(out), nil
        })

        // --- adb_read_file ---
        s.AddTool(mcp.NewTool("adb_read_file",
                mcp.WithDescription("Read a file from the An
  filesystem. Useful for reading crash.txt, SQLite DB dumps,
   etc."),
                mcp.WithString("path", mcp.Required(),
  mcp.Description("Absolute path on device, e.g.
  /data/data/org.example.autobookkeeping/files/crash.txt")),
        ), func(ctx context.Context, req mcp.CallToolRequest
  (*mcp.CallToolResult, error) {
                path, _ := req.Params.Arguments["path"].(str
                out, err := runADB("shell", "run-as",
  "org.example.autobookkeeping", "cat", path)
                if err != nil {
                        // fallback without run-as (for non-
                        out2, err2 := runADB("shell", "cat",
                        if err2 != nil {
                                return mcp.NewToolResultText
  err.Error() + "\nerror (direct): " + err2.Error()), nil
                        }
                        return mcp.NewToolResultText(out2),
                }
                return mcp.NewToolResultText(out), nil
        })

        // --- adb_shell ---
        s.AddTool(mcp.NewTool("adb_shell",
                mcp.WithDescription("Run an arbitrary adb sh
   the device. Use for querying SQLite, checking
  permissions, sending test broadcasts, etc."),
                mcp.WithString("command", mcp.Required(),
  mcp.Description("Shell command to run, e.g. 'sqlite3 /data
  /data/org.example.autobookkeeping/files/bookkeeping.db
  \".tables\"'")),
        ), func(ctx context.Context, req mcp.CallToolRequest
  (*mcp.CallToolResult, error) {
                command, _ := req.Params.Arguments["command"
                if command == "" {
                        return mcp.NewToolResultText("error:
  required"), nil
                }
                // Split command for exec
                parts := splitCommand(command)
                ctx2, cancel := context.WithTimeout(context.
  30*time.Second)
                defer cancel()
                args := append([]string{"shell"}, parts...)
                cmd := exec.CommandContext(ctx2, "adb", args
                out, err := cmd.CombinedOutput()
                result := string(out)
                if err != nil {
                        result = "exit error: " + err.Error(
                }
                return mcp.NewToolResultText(result), nil
        })

        // --- adb_install_apk ---
        s.AddTool(mcp.NewTool("adb_install_apk",
                mcp.WithDescription("Install an APK file ont
  connected Android device"),
                mcp.WithString("apk_path", mcp.Required(),
  mcp.Description("Local path to the APK file, e.g.
  /Users/l/Desktop/Automatic-bookkeeping/bin/autobookkeeping
  -1.13.2-arm64-v8a-debug.apk")),
        ), func(ctx context.Context, req mcp.CallToolRequest
  (*mcp.CallToolResult, error) {
                apkPath, _ := req.Params.Arguments["apk_path
                if _, err := os.Stat(apkPath); os.IsNotExist
                        return mcp.NewToolResultText("error:
   + apkPath), nil
                }
                ctx2, cancel := context.WithTimeout(context.
  120*time.Second)
                defer cancel()
                cmd := exec.CommandContext(ctx2, "adb", "ins
  apkPath)
                out, err := cmd.CombinedOutput()
                result := string(out)
                if err != nil {
                        result = "install error: " + err.Err
                }
                return mcp.NewToolResultText(result), nil
        })

        // --- adb_logcat_stream (streaming, for live captur
        s.AddTool(mcp.NewTool("adb_logcat_clear",
                mcp.WithDescription("Clear the logcat buffer
   so next capture starts fresh"),
        ), func(ctx context.Context, req mcp.CallToolRequest
  (*mcp.CallToolResult, error) {
                out, err := runADB("logcat", "-c")
                if err != nil {
                        return mcp.NewToolResultText("error:
                }
                return mcp.NewToolResultText("cleared. " + o
        })

        _ = json.Marshal // suppress unused import
        _ = bufio.NewReader(nil)

        if err :=
  server.NewStdioServer(s).Listen(context.Background(),
  os.Stdin, os.Stdout); err != nil {
                fmt.Fprintf(os.Stderr, "server error: %v\n",
                os.Exit(1)
        }
  }

  // splitCommand splits a shell command string into args,
  respecting quoted strings
  func splitCommand(s string) []string {
        var args []string
        var current strings.Builder
        inQuote := false
        quoteChar := byte(0)
        for i := 0; i < len(s); i++ {
                c := s[i]
                if inQuote {
                        if c == quoteChar {
                                inQuote = false
                        } else {
                                current.WriteByte(c)
                        }
                } else if c == '"' || c == '\'' {
                        inQuote = true
                        quoteChar = c
                } else if c == ' ' || c == '\t' {
                        if current.Len() > 0 {
                                args = append(args, current.
                                current.Reset()
                        }
                } else {
                        current.WriteByte(c)
                }
        }
        if current.Len() > 0 {
                args = append(args, current.String())
        }
        return args
  }

  // go.mod
  module android-adb-bridge

  go 1.21

  require github.com/mark3labs/mcp-go v0.17.0

  ---
  使用方式

  # 1. 创建目录并放入上面两个文件
  mkdir ~/mcp-adb && cd ~/mcp-adb
  # 放入 main.go 和 go.mod

  # 2. 下载依赖并编译
  go mod tidy
  go build -o mcp-adb-bridge .

  # 3. 在 Claude Code 的 MCP 配置里挂载
  # ~/.claude/settings.json 或 claude_desktop_config.json
  加入：
  {
    "mcpServers": {
      "android-adb": {
        "command": "/Users/l/mcp-adb/mcp-adb-bridge",
        "args": []
      }
    }
  }

  挂载后，手机通过 USB 连接并开启 USB 调试，我就能直接：
  - 读 crash.txt 看 Python 异常
  - 抓 logcat 看 Java 服务是否触发
  - 查 SQLite 看数据有没有写入
  - 发测试广播验证 BroadcastReceiver 是否存活