# 自动化测试框架使用说明

本文档说明 `automation/` 目录下自动化测试脚本的使用方式。

## 目标流程

当前自动化框架覆盖的流程是：

1. 本机启动 gNB。
2. SSH 到远端机器启动 UE。
3. 轮询 UE 侧 `oaitun_ue1`，直到接口出现并拿到 IPv4。
4. 从 UE 侧发起 `iperf3` 测试。
5. 可选地在本机或 UE 侧加 `stress-ng` 负载。
6. 保存 gNB / UE / iperf / stress 日志和本次测试摘要。

## 目录结构

- `run_test.py`
  单次测试入口。
- `run_batch.py`
  批量测试入口，适合一夜跑多轮。
- `config.example.json`
  单次测试配置样例。
- `config.batch.example.json`
  批量测试配置样例。
- `runs/`
  单次测试输出目录。
- `batches/`
  批量测试输出目录。

## 前置条件

运行前建议确认以下条件：

1. 本机能正常启动 gNB。
2. 本机能免密 SSH 到 UE 服务器。
3. UE 服务器上能正常启动 UE。
4. `iperf3` 已安装在 UE 侧。
5. 如需加负载，目标机器上已安装 `stress-ng`。
6. 配置中的 `sudo` 命令不需要交互输入密码。

## sudo 建议

自动化脚本是非交互方式启动进程，所以不要依赖手工输入 sudo 密码。

推荐在本机和远端 UE 机器上配置免密 sudo，并在配置文件里使用：

```bash
sudo -n /usr/bin/bash /absolute/path/to/script.sh
```

例如：

```json
"start_command": "sudo -n /usr/bin/bash /home/ubuntu/hcs/ran/cmake_targets/run_gNB.sh"
```

## SSH 建议

`ue.ssh_target` 的格式和普通 `ssh` 命令一致，推荐两种写法：

1. 直接写 `user@ip`
2. 写 `~/.ssh/config` 中已经配置好的 Host 别名

例如：

```json
"ssh_target": "bupt@10.156.64.40"
```

## 单次测试

### 运行命令

```bash
cd /home/ubuntu/hcs/ran
python3 automation/run_test.py --config automation/config.example.json
```

### 运行时终端输出

脚本运行时会直接向终端输出过程日志，便于调试，典型内容包括：

- 当前是第几次 bring-up 尝试
- gNB 已启动，正在等待初始化
- UE 已启动，正在等待 `oaitun_ue1`
- `oaitun_ue1` 已获取到 IP
- `iperf3` 开始执行和结束
- 已发送 `SIGTERM` / `SIGKILL` 清理 gNB、UE、stress 相关进程
- 本次测试失败原因

### 单次配置文件说明

`config.example.json` 主要分为五部分：

#### 1. `gnb`

用于本机启动 gNB。

常用字段：

- `workdir`
  启动命令执行目录。
- `start_command`
  启动 gNB 的命令，建议写绝对路径。
- `stop_command`
  停止 gNB 的命令，推荐使用 `sudo -n pkill -KILL -f ...`。
- `log_source_path`
  gNB 真实业务日志所在路径；脚本会在停止 gNB 后从这里复制日志。
- `startup_wait_sec`
  启动后等待几秒，再继续执行后续步骤。
- `max_retries`
  gNB/UE bring-up 失败时的最大重试次数。
- `retry_delay_sec`
  每次重试前等待秒数。

示例：

```json
"gnb": {
  "workdir": "/home/ubuntu/hcs/ran/cmake_targets",
  "start_command": "sudo -n /usr/bin/bash /home/ubuntu/hcs/ran/cmake_targets/run_gNB.sh",
  "stop_command": "sudo -n /usr/bin/pkill -KILL -f /home/ubuntu/hcs/ran/cmake_targets/ran_build/build/nr-softmodem",
  "log_source_path": "/tmp/oai-automation/gnb.log",
  "startup_wait_sec": 8,
  "max_retries": 2,
  "retry_delay_sec": 10
}
```

#### 2. `ue`

用于 SSH 到远端启动 UE。

常用字段：

- `ssh_target`
  UE 远端登录目标。
- `workdir`
  远端执行目录。
- `start_command`
  远端启动 UE 的命令。
- `stop_command`
  远端停止 UE 的命令，推荐使用 `sudo -n pkill -KILL -f ...`。
- `continue_on_start_timeout`
  如果远端启动命令没有顺利返回 PID，是否仍继续进入 `oaitun_ue1` 检测。
- `log_source_path`
  UE 真实业务日志所在路径；脚本会在停止 UE 后从远端复制日志。
- `tun_interface`
  默认是 `oaitun_ue1`。
- `ready_timeout_sec`
  等待 `oaitun_ue1` 拿到 IP 的最大时间。
- `poll_interval_sec`
  轮询时间间隔。
- `remote_log_path`
  远端 UE 日志保存位置。

示例：

```json
"ue": {
  "ssh_target": "bupt@10.156.64.40",
  "workdir": "/home/bupt/wlh/openairinterface5g_2025_w10",
  "start_command": "sudo -n /usr/bin/bash /home/bupt/wlh/openairinterface5g_2025_w10/run_nrUE.sh",
  "stop_command": "sudo -n /usr/bin/pkill -KILL -f nr-uesoftmodem",
  "log_source_path": "/tmp/oai-automation/ue.log",
  "continue_on_start_timeout": true,
  "tun_interface": "oaitun_ue1",
  "ready_timeout_sec": 20,
  "poll_interval_sec": 5,
  "remote_log_path": "/tmp/oai-automation/ue_start.log"
}
```

#### 3. `iperf_server`

指定 `iperf3 server` 的位置。

支持三种模式：

- `external`
  脚本不启动 server，直接连接已有服务器。
- `local`
  脚本在本机启动 server。
- `remote`
  脚本在远端机器启动 server。

如果你的 server 已经固定存在，例如 `10.129.9.235`，建议：

```json
"iperf_server": {
  "mode": "external",
  "host_for_client": "10.129.9.235",
  "port": 5201
}
```

#### 4. `iperf_client`

用于配置 UE 侧 `iperf3`。

常用字段：

- `duration_sec`
  测试时长。
- `protocol`
  `tcp` 或 `udp`。
- `reverse`
  是否使用 `-R`。
- `bitrate`
  仅 UDP 时有效。
- `bind_to_tunnel_ip`
  是否自动绑定到 `oaitun_ue1` 获取到的 IP。
- `extra_args`
  额外 `iperf3` 参数。
- `remote_log_path`
  远端 iperf 日志路径。

示例：

```json
"iperf_client": {
  "duration_sec": 100,
  "protocol": "tcp",
  "reverse": false,
  "bitrate": "100M",
  "bind_to_tunnel_ip": true,
  "extra_args": [
    "--json"
  ],
  "remote_log_path": "/tmp/oai-automation/iperf_client.log"
}
```

说明：

- 当 `bind_to_tunnel_ip=true` 时，脚本会自动获取 UE 侧 `oaitun_ue1` 的 IP，并用于 `iperf3 -B <ue_ip>`。
- 这适合 UE 侧隧道地址不固定的场景。
- 如果你的现场标准就是“20 秒内 `oaitun_ue1` 没有 IP 就视为失败重试”，那就把 `ue.ready_timeout_sec` 设为 `20`。
- `remote_log_path` 现在表示“UE 启动命令的 stdout/stderr 日志”，真正的业务日志请放在 `log_source_path`。

#### 5. `stress`

可选，用于测试阶段加压力。

常用字段：

- `enabled`
  是否启用。
- `target`
  `local` 或 `ue`。
- `command`
  直接指定完整的 `stress-ng` 启动命令；如果配置了它，`cpu_workers` 等参数会被忽略。
- `duration_sec`
  压力持续时间。
- `cpu_workers`
  `stress-ng --cpu` worker 数量。
- `cpu_load`
  CPU 负载百分比。
- `extra_args`
  额外参数。
- `remote_log_path`
  远端压测日志位置。

示例：

```json
"stress": {
  "enabled": true,
  "target": "local",
  "command": "taskset -c 0-7 stress-ng --cache 10 --cache-level 3 --timeout 6000s --metrics-brief",
  "remote_log_path": "/tmp/oai-automation/stress.log"
}
```

如果你希望施加缓存负载而不是纯 CPU 负载，推荐直接使用 `command`，例如：

```bash
taskset -c 0-7 stress-ng --cache 10 --cache-level 3 --timeout 6000s --metrics-brief
```

## gNB 初始化失败后的自动重试

脚本已支持 bring-up 阶段自动重试。

触发重试的阶段包括：

- gNB 启动后很快退出
- UE 启动后 `oaitun_ue1` 一直没有拿到 IP
- gNB 在 UE attach 前提前退出

重试行为：

1. 清理本次 gNB / UE 进程
2. 等待 `gnb.retry_delay_sec`
3. 重新启动 gNB 和 UE

相关参数：

```json
"gnb": {
  "max_retries": 2,
  "retry_delay_sec": 10
}
```

这表示：

- 第 1 次尝试失败后，再试 2 次
- 总共最多 3 次 bring-up

## 批量测试

当你要跑很多轮测试，例如：

- 3 种 stress 模式
- 每种模式 10 次
- 总共 30 次

就应该用批量脚本。

### 运行命令

```bash
cd /home/ubuntu/hcs/ran
python3 automation/run_batch.py --batch-config automation/config.batch.example.json
```

### 批量配置文件结构

批量配置由三部分组成：

1. `base_config`
   指向单次测试配置文件。
2. `scenarios`
   定义不同 stress 场景。
3. `repeat`
   每个场景重复次数。

示例：

```json
{
  "batch_name": "night_30runs",
  "base_config": "automation/config.example.json",
  "artifacts_root": "automation/batches",
  "continue_on_failure": true,
  "scenarios": [
    {
      "name": "cache_light",
      "repeat": 10,
      "overrides": {
        "stress": {
          "enabled": true,
          "target": "local",
          "command": "taskset -c 0-3 stress-ng --cache 4 --cache-level 3 --timeout 6000s --metrics-brief"
        }
      }
    },
    {
      "name": "cache_medium",
      "repeat": 10,
      "overrides": {
        "stress": {
          "enabled": true,
          "target": "local",
          "command": "taskset -c 0-7 stress-ng --cache 8 --cache-level 3 --timeout 6000s --metrics-brief"
        }
      }
    },
    {
      "name": "cache_heavy",
      "repeat": 10,
      "overrides": {
        "stress": {
          "enabled": true,
          "target": "local",
          "command": "taskset -c 0-7 stress-ng --cache 10 --cache-level 3 --timeout 6000s --metrics-brief"
        }
      }
    }
  ]
}
```

这份计划会执行：

- `stress_light` 10 次
- `stress_medium` 10 次
- `stress_heavy` 10 次

总计 30 次。

### 批量输出

批量运行结果会写到：

```text
automation/batches/<timestamp>_<batch_name>/
```

目录中通常包括：

- `batch_config.json`
- `batch_summary.json`
- `batch_results.csv`
- `runs/`

其中 `runs/` 下每一轮测试都会有独立目录。

## 输出文件说明

单次运行目录通常包含：

- `input_config.json`
- `summary.json`
- `gnb.log`
- `gnb_start.log`
- `ue.log`
- `ue_start.log`
- `iperf_client.log`
- `stress.log`

如果启用了 bring-up 重试，还可能看到：

- `gnb_attempt01.log`
- `gnb_attempt02.log`
- `ue_attempt01.log`
- `ue_attempt02.log`

`summary.json` 中常见字段：

- `status`
  `ok` 或 `failed`
- `ue_ip`
  本次获取到的 UE IP
- `iperf.mbps`
  解析出的吞吐
- `gnb_attempts_used`
  bring-up 最终用了几次尝试
- `bringup_failures`
  每次失败的错误信息

## 常见问题

### 1. 脚本看起来一直不退出

这通常不是卡死，而是在等待某个阶段完成：

- 等 gNB 启动
- 等 UE 拿到 `oaitun_ue1`
- 等 `iperf3` 跑完

重点检查：

- `ready_timeout_sec`
- `iperf_client.duration_sec`
- 当前运行目录下的 `gnb.log` 和 `ue.log`

### 2. `sudo: a password is required`

说明当前命令虽然用了 `sudo -n`，但免密 sudo 规则没有匹配上。

最常见原因：

- `sudoers` 里配置的是绝对路径，但脚本里调用的是相对路径
- `sudoers` 里放行的是脚本路径，实际执行的却是 `bash ./script.sh`

建议统一使用绝对路径命令，例如：

```bash
sudo -n /usr/bin/bash /home/ubuntu/hcs/ran/cmake_targets/run_gNB.sh
```

停止命令建议也显式配置，例如：

```bash
sudo -n /usr/bin/pkill -KILL -f /home/ubuntu/hcs/ran/cmake_targets/ran_build/build/nr-softmodem
sudo -n /usr/bin/pkill -KILL -f nr-uesoftmodem
```

### 3. UE 一直拿不到 `oaitun_ue1`

检查：

- UE 是否真的成功启动
- 远端 `start_command` 是否正确
- `tun_interface` 名称是否正确
- gNB 是否已完成初始化

### 4. `stress-ng` 启动失败

检查对应目标机器上是否已安装：

```bash
command -v stress-ng
```

### 5. `iperf3` 吞吐结果为空

检查：

- `iperf3 server` 地址是否可达
- `host_for_client` 是否正确
- `bind_to_tunnel_ip` 是否需要开启
- `iperf_client.log` 中是否有实际输出

## 建议的运行顺序

为了减少一夜批跑失败的概率，建议按以下顺序验证：

1. 手工验证本机 gNB 启动命令
2. 手工验证远端 UE 启动命令
3. 手工验证 UE 侧能看到 `oaitun_ue1`
4. 手工验证 UE 到 `iperf3 server` 的连通性
5. 先跑 1 次 `run_test.py`
6. 再跑 `run_batch.py`

## 推荐做法

如果你今晚计划跑 30 次，建议：

1. 先把单次测试跑通。
2. `iperf_client.duration_sec` 用正式值，例如 `100`。
3. `gnb.max_retries` 设置为 `2` 或 `3`。
4. `continue_on_failure` 设为 `true`，避免一轮失败后整批终止。
5. 批跑前确认磁盘空间足够保存日志。
