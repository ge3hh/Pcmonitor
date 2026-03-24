"""Full test suite for Pcmonitor project"""
import py_compile
import ast
import sys
import os

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

files = [
    'main.py',
    'core/__init__.py',
    'core/cpu_monitor.py', 'core/memory_monitor.py', 'core/disk_monitor.py',
    'core/network_monitor.py', 'core/gpu_monitor.py', 'core/process_monitor.py',
    'core/data_collector.py',
    'utils/__init__.py', 'utils/config.py', 'utils/database.py', 'utils/alert_manager.py',
    'ui/main_window.py', 'ui/monitor_widget.py', 'ui/gauge_widget.py',
    'ui/settings_dialog.py', 'ui/process_dialog.py', 'ui/history_dialog.py',
]

total_pass = 0
total_fail = 0

def check(ok, msg):
    global total_pass, total_fail
    if ok:
        total_pass += 1
        print(f'  OK: {msg}')
    else:
        total_fail += 1
        print(f'  FAIL: {msg}')

# === Test 1: Syntax ===
print('=== 1. Syntax Compilation Test ===')
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        check(True, f)
    except Exception as e:
        check(False, f'{f} - {e}')

# === Test 2: Bare except ===
print('\n=== 2. Bare Except Check ===')
bare_count = 0
for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        tree = ast.parse(fh.read(), filename=f)
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            print(f'  WARN: {f}:{node.lineno} - bare except')
            bare_count += 1
check(bare_count == 0, f'No bare except ({bare_count} found)')

# === Test 3: Import consistency ===
print('\n=== 3. Logging Import Check ===')
for f in ['core/cpu_monitor.py', 'core/gpu_monitor.py', 'core/disk_monitor.py',
          'core/data_collector.py', 'utils/config.py', 'utils/database.py']:
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    check('import logging' in content, f'{f} has logging')

# === Test 4: Fix Verification ===
print('\n=== 4. Fix Verification ===')

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

alert = read_file('utils/alert_manager.py')
check('popup_requested' in alert, '#1 - popup_requested signal')
check("alert_key = alert_info['type']" in alert, '#5 - alert_key by resource type')

mw = read_file('ui/monitor_widget.py')
check('self.data_callback is not self.value_callback' in mw, '#2 - data_callback in update_display')

nm = read_file('core/network_monitor.py')
check('time.sleep' not in nm, '#3 - no time.sleep in network_monitor')

dc = read_file('core/data_collector.py')
check('disk_read_mb' in dc and 'disk_write_mb' in dc, '#4 - disk IO rate in data_collector')

hd = read_file('ui/history_dialog.py')
check('DateAxisItem' in hd, '#6 - DateAxisItem in history charts')
check('#FF980O' not in hd and '#FF9800' in hd, '#7 - color code fixed')

sd = read_file('ui/settings_dialog.py')
check('validate_thresholds' in sd, '#8 - threshold validation')

pd = read_file('ui/process_dialog.py')
check('psutil.pids()' in pd, '#9 - total process count')

cfg = read_file('utils/config.py')
check('self._lock' in cfg and 'Lock' in cfg, '#11 - Config threading.Lock')
check('_validate_config' in cfg, '#12 - Config schema validation')

db_content = read_file('utils/database.py')
check('VACUUM' in db_content, '#13 - Database VACUUM')

main_content = read_file('main.py')
check('logging.basicConfig' in main_content, '#10 - logging init in main.py')

# === Test 5: Config Validation Unit Test ===
print('\n=== 5. Config Validation Unit Test ===')
# Direct import to avoid PyQt5 dependency chain via utils/__init__.py
import importlib.util
spec = importlib.util.spec_from_file_location('config', 'utils/config.py')
config_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_mod)
Config = config_mod.Config

c = Config()
check(isinstance(c.get('update_interval'), (int, float)), 'Default config loads correctly')
check(c.get('theme') in ('dark', 'light'), 'Theme is valid')

bad = {'update_interval': 'abc', 'theme': 'neon', 'minimal_mode': 42}
v = c._validate_config(bad)
check(isinstance(v['update_interval'], float), 'Invalid update_interval corrected')
check(v['theme'] in ('dark', 'light'), 'Invalid theme corrected')
check(isinstance(v['minimal_mode'], bool), 'Invalid minimal_mode corrected')

# Test threshold validation
bad_thresh = {
    'update_interval': 1.0, 'theme': 'dark', 'minimal_mode': False,
    'monitors': {}, 'window_always_on_top': False, 'start_minimized': False,
    'alerts': {'thresholds': {'cpu': {'warning': 95, 'danger': 80}}}
}
v2 = c._validate_config(bad_thresh)
cpu_t = v2['alerts']['thresholds']['cpu']
check(cpu_t['warning'] < cpu_t['danger'], 'Invalid threshold (warning>danger) corrected')

c.set('_test_key', 'test_value')
check(c.get('_test_key') == 'test_value', 'Thread-safe set/get works')
c.config.pop('_test_key', None)
c.save_config()

# === Test 6: Database Unit Test ===
print('\n=== 6. Database Unit Test ===')
spec2 = importlib.util.spec_from_file_location('database', 'utils/database.py')
db_mod = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(db_mod)
HistoryDatabase = db_mod.HistoryDatabase

db = HistoryDatabase()
test_data = {
    'cpu_percent': 45.5, 'memory_percent': 60.2, 'memory_used_gb': 8.1,
    'disk_percent': 55.0, 'disk_read_mb': 12.5, 'disk_write_mb': 3.2,
    'network_up_mb': 0.5, 'network_down_mb': 1.2,
    'gpu_percent': 30.0, 'gpu_memory_percent': 25.0
}
db.insert_record(test_data)
check(True, 'Record inserted')

recent = db.get_recent_data(minutes=1)
check(len(recent) > 0, 'Recent data returned')

last = recent[-1]
check(abs(last['cpu_percent'] - 45.5) < 0.01, 'cpu_percent stored correctly')
check(abs(last['disk_read_mb'] - 12.5) < 0.01, 'disk_read_mb NOT NULL (fix #4)')
check(abs(last['disk_write_mb'] - 3.2) < 0.01, 'disk_write_mb NOT NULL (fix #4)')
check(abs(last['memory_used_gb'] - 8.1) < 0.01, 'memory_used_gb NOT NULL (fix #4)')

stats = db.get_statistics(hours=1)
check(stats['avg_cpu'] > 0, 'Statistics query works')

# === Summary ===
print('\n' + '=' * 40)
print(f'TOTAL: {total_pass} passed, {total_fail} failed')
if total_fail == 0:
    print('ALL TESTS PASSED')
else:
    print(f'{total_fail} TESTS FAILED')
    sys.exit(1)
