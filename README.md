# Three-Way-Decision-Preservation-Certification-in-Multi-Layer-Granular-Ball-Attribute-Selection
原实验环境为 Windows、Python 3.12.14。建议使用 Python 3.12；入口会拒绝低于3.12的版本。冻结清单中保留Windows路径格式，因此本包的复现验证范围为Windows。目录可整体复制，但须保留内部相对路径。

核心算法、数据预处理、实验驱动与核对入口使用Python标准库，不需要GPU或在线下载数据。历史可视化脚本并非复现实验所必需，单独运行时可能需要matplotlib。可选的psutil若已安装，原单次运行器可能据此尝试设置CPU亲和性，并将结果记入日志；论文原计时未固定亲和性。

双击“启动菜单.bat”可选择现有核验与实验命令。菜单会查找Python 3.12启动器、可用的配套环境或兼容的默认解释器；若未找到，应先安装Python 3.12。以下命令中的python必须指向符合要求的解释器。

建议执行顺序
TEXT
复制
python 运行入口.py verify
python 核对论文结果.py
python 运行入口.py quick
