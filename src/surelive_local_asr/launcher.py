import subprocess, sys
from pathlib import Path
subprocess.Popen([str(Path(sys.executable).parent / 'SureLive-NativeHost.exe'), '--gui'], creationflags=subprocess.CREATE_NO_WINDOW)
