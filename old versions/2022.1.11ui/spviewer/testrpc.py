
import CmdFIFO_py3 as CmdFIFO

port = 50070
url = 'http://10.100.4.20'    ## URL (web address)
# url = 'http://1022.corp.picarro.com'  ##works too
# MeasSystem = CmdFIFO.CmdFIFOServerProxy(f"http://localhost:{port}", "test_connection", IsDontCareConnection=False)
MeasSystem = CmdFIFO.CmdFIFOServerProxy(f"{url}:{port}", "test_connection", IsDontCareConnection=False)
print(MeasSystem.GetStates())


# MeasSystem.Backdoor.SetData('my_var',50)
# print(MeasSystem.Backdoor.GetData('my_var'))







