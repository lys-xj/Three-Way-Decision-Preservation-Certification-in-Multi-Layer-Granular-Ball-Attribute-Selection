"""Portable launcher for the unmodified TailCert-L-IE-v0.4 research code.

All new runs use a fresh extraction; archived publication results stay intact.
Only the Python standard library is needed for the commands in this file.
"""
from pathlib import Path
from datetime import datetime
import argparse
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
import zipfile

sys.dont_write_bytecode = True
PACKAGE_DIR = Path(__file__).resolve().parent
SOURCE = PACKAGE_DIR / '研究实现'
S18 = '第18步_最终算法正式实验'
S28 = '第28步_末层节点认证开关补充实验'
S19 = '第19步_证明与代码最终核验'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    spec = importlib.util.spec_from_file_location('delivered_formal_driver', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def inside(base, relative):
    dest = (base / relative).resolve()
    if not dest.is_relative_to(base.resolve()):
        raise ValueError('路径超出复现目录: ' + str(relative))
    return dest


def verify():
    manifest = read(PACKAGE_DIR / '文件校验清单.json')
    for row in manifest['files']:
        path = inside(PACKAGE_DIR, row['path'])
        if not path.is_file() or sha(path) != row['sha256']:
            raise RuntimeError('文件缺失或已修改: ' + row['path'])
    mod = load(SOURCE / S18 / '198_统一实验驱动.py')
    mod.verify_lock()
    datasets = read(SOURCE / S18 / '197_公共数据清单.json')['datasets']
    for row in datasets:
        for name, digest in [('原始数据/' + row['key'] + '.zip', row['source_archive_sha256']),
                             ('待实验数据/' + row['key'] + '_exact.json', row['prepared_sha256'])]:
            if sha(SOURCE / S18 / name) != digest:
                raise RuntimeError('数据校验不一致: ' + name)
    records = 0
    for folder, name, key in [(S18, '209_正式实验汇总.json', 'raw_files_sha256'),
                              (S28, '补充实验汇总.json', 'raw_hashes')]:
        for name, digest in read(SOURCE / folder / name)[key].items():
            if sha(SOURCE / folder / name) != digest:
                raise RuntimeError('原始实验记录校验不一致: ' + name)
            records += 1
    expected = read(PACKAGE_DIR / '论文对应信息.json')
    summary = read(SOURCE / S18 / '209_正式实验汇总.json')
    table1 = []
    for row in summary['main']:
        tc, local = row['methods']['TC'], row['methods']['L']
        t = tc['times']['decision_only_seconds']['median']
        l = local['times']['decision_only_seconds']['median']
        table1.append([f"{row['n']}/{row['d']}", str(len(tc['final_attributes'])),
                       str(tc['candidate_count']), f"{row['pass_count']}/{tc['metrics']['certificate_attempts']}",
                       f'{l:.3f}', f'{t:.3f}', f'{t/l:.3f}'])
    table2 = []
    for row in read(SOURCE / S28 / '补充实验汇总.json')['rows']:
        table2.append([str(row['node_calls']), f"{row['full_rounds']}→{row['on_rounds']}",
                       f"{row['methods']['OFF']['median']:.4f}", f"{row['methods']['ON']['median']:.4f}",
                       f"{row['ratio']:.3f}"])
    if table1 != expected['table1_numeric_cells'] or table2 != expected['table2_numeric_cells']:
        raise RuntimeError('论文表格与归档实验记录不一致')
    print(f"校验通过：{len(manifest['files'])}个文件、8套数据、{records}份原始记录；论文表1和表2一致。", flush=True)
    return {'files': len(manifest['files']), 'datasets': 8, 'raw_records': records,
            'paper_tables_match': True}


def fresh(mode):
    run = PACKAGE_DIR / '复现运行' / (datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '_' + mode)
    run.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(PACKAGE_DIR / '从零复现实验模板.zip') as archive:
        for info in archive.infolist():
            inside(run, info.filename)
        archive.extractall(run)
    (run / '本次运行说明.json').write_text(json.dumps({
        'mode': mode, 'started': datetime.now().isoformat(), 'python': sys.version,
        'platform': platform.platform(), 'fresh_results': True,
        'original_source': '研究实现', 'timing_not_expected_to_equal_publication': True
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print('本次新结果目录：' + str(run), flush=True)
    return run


def call(path, *args):
    env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
    subprocess.run([sys.executable, str(path), *map(str, args)], check=True,
                   cwd=path.parent, env=env, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))


def quick(run):
    out = run / 'Banknote_独立核验.json'
    call(run / S18 / '199_单次正式实验.py', '--dataset', 'banknote', '--method', 'TC',
         '--setting', 'main', '--phase', 'audit', '--output', out)
    expected = next(r for r in read(SOURCE / S18 / '209_正式实验汇总.json')['main'] if r['key'] == 'banknote')
    result = read(out)
    if result['output_fingerprint'] != expected['methods']['TC']['fingerprint']:
        raise RuntimeError('Banknote完整搜索输出与论文记录不一致')
    # Use all eight archived Blood calls for a small, separately timed mechanism check.
    snapshot = run / S28 / 'blood_节点.json'
    snapshot.write_bytes((SOURCE / S28 / snapshot.name).read_bytes())
    for method in ('OFF', 'ON'):
        call(run / S28 / '节点重放.py', 'timed', '--dataset', 'blood', '--method', method, '--repeat', '0')
    data = {'status': 'passed', 'banknote_full_search_and_independent_audit': True,
            'banknote_fingerprint': result['output_fingerprint'],
            'blood_node_calls_each_method': 8, 'methods': ['OFF', 'ON'],
            'scope': '代表性完整搜索与8个节点的双方法重放；不是重跑全部正式实验。'}
    (run / '快速核验结果.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print('快速核验通过；决定及搜索结果一致，计时数值不要求与论文相同。', flush=True)


def prepare(run):
    call(run / '第6步_实验方案与创新性复核' / '32_数据核查与预处理.py')
    call(run / S18 / '196_准备公共数据.py')
    # Compare generated content and byte identities, not just sample counts.
    for row in read(SOURCE / S18 / '197_公共数据清单.json')['datasets']:
        name = row['key'] + '_exact.json'
        if sha(run / S18 / '待实验数据' / name) != row['prepared_sha256']:
            raise RuntimeError('重新预处理后数据不一致: ' + name)
    print('8套数据从原始压缩包重新计算，均与论文输入一致。', flush=True)


def main_experiments(run):
    for name in ['200_串行执行与恢复.py', '206_Banknote整块重测.py',
                 '208_汇总与一致性检查.py', '227_追加非拒绝认证核验.py']:
        call(run / S18 / name)


def menu():
    options = {'1': 'verify', '2': 'quick', '3': 'prepare', '4': 'table2',
               '5': 'table1', '6': 'proof', '7': 'full'}
    print('1 文件/论文数字校验\n2 快速核验\n3 从原始数据重做预处理\n4 重跑表2\n5 重跑主实验及追加核验\n6 证明边界核验\n7 全部实验（耗时较长）\n0 退出')
    answer = input('请输入编号：').strip()
    if answer == '0':
        return None
    if answer not in options:
        raise ValueError('无效编号')
    return options[answer]


def main():
    if sys.flags.optimize:
        raise RuntimeError('请勿使用 python -O，算法核验需要保留断言。')
    if sys.version_info < (3, 12):
        raise RuntimeError('请使用Python 3.12或更新版本；论文使用3.12.14。')
    parser = argparse.ArgumentParser(description='论文数据与源代码的统一入口')
    parser.add_argument('mode', nargs='?', default='menu',
                        choices=['menu', 'verify', 'quick', 'prepare', 'table1', 'table2', 'proof', 'full'])
    mode = parser.parse_args().mode
    if mode == 'menu':
        mode = menu()
    if mode is None:
        return
    verify()
    if mode == 'verify':
        return
    run = fresh(mode)
    if mode in ('quick', 'prepare'):
        {'quick': quick, 'prepare': prepare}[mode](run)
    if mode in ('table1', 'full'):
        main_experiments(run)
    if mode in ('table2', 'full'):
        if mode == 'table2':
            # Reference search fingerprints are read-only inputs, not new timing results.
            (run / S18 / '209_正式实验汇总.json').write_bytes((SOURCE / S18 / '209_正式实验汇总.json').read_bytes())
        call(run / S28 / '节点重放.py', 'run')
    if mode in ('proof', 'full'):
        call(run / S19 / '234_证明边界独立核验.py')
    print('运行完成。结果已保存到：' + str(run), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('运行未完成：' + str(exc), file=sys.stderr)
        sys.exit(1)
