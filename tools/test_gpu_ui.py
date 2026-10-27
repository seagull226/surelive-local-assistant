"""Exercise real Tk controls through the app's test driver, using isolated host state."""
import json, threading, traceback
from pathlib import Path
from types import SimpleNamespace
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/surelive_local_asr'))
from desktop import run_gui

def run(output):
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'artifacts'):raise ValueError('Use a new artifacts directory')
    output.mkdir(parents=True)
    host=SimpleNamespace(DATA=output,settings={},settings_file=output/'settings.json',jobs={},hardware={'preferred':'cpu'},
        catalog=json.loads((ROOT/'resources/models.json').read_text()),models=SimpleNamespace(root=output/'models',ready=lambda _:False),
        gpu=SimpleNamespace(status={'preferred':'cpu','state':'needed','cudaDevices':1,'source':'none'}))
    called=threading.Event()
    def begin(model,**kwargs):
        job={'model':model,'stage':'preparing','finished':False};host.jobs['one']=job;return 'one',job
    def prepare(job):
        assert job['gpuOnly'];job.update(stage='complete',finished=True);called.set()
    host.begin=begin;host.run=prepare;host.stop=lambda job:job.update(finished=True)
    result={}
    def driver(app,api):
        try:
            w=api['widgets'];api['update']()
            assert w['gpu_prepare']['state']=='normal'
            assert 'NVIDIA' in w['hardware']['text']
            w['cpu_only'].invoke()
            assert host.settings['accelerationMode']=='cpu'
            assert json.loads(host.settings_file.read_text())['accelerationMode']=='cpu'
            assert 'CPU' in w['hardware']['text']
            w['cpu_only'].invoke();assert host.settings['accelerationMode']=='auto'
            w['gpu_prepare'].invoke();assert called.wait(3)
            api['update']();result['prepareButtonCallsGpuPreparation']=True
            host.gpu.status={'preferred':'cuda','state':'ready','cudaDevices':1,'source':'system'};api['update']()
            assert '复用本机' in w['hardware']['text'];assert w['gpu_prepare']['state']=='disabled'
            w['language'].set('English');api['language']();api['update']()
            assert 'reusing' in w['hardware']['text'];assert 'CPU only' in w['cpu_only']['text']
            app.update_idletasks()
            assert w['cpu_only'].winfo_reqwidth() <= w['cpu_only'].master.winfo_width()
            host.gpu.status={'preferred':'cpu','state':'cpu','cudaDevices':0,'source':'none'};api['update']()
            assert w['gpu_prepare']['state']=='disabled';assert 'CPU mode' in w['hardware']['text']
            result.update(cpuSettingPersists=True,systemReuseState=True,noGpuState=True,bilingualControls=True,
                          controlFitsPanel=True,visualScreenshotVerified=False)
        except Exception:result['error']=traceback.format_exc()
        finally:
            (output/'result.json').write_text(json.dumps(result,indent=2));api['quit']()
    run_gui(host,driver)
    print(json.dumps(result));assert 'error' not in result,result.get('error')

if __name__=='__main__':run(Path(sys.argv[1]))
