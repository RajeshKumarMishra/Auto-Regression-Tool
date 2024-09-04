###############################################################################
# Import Libs
###############################################################################

from Local.Libs.BiosMenu.BiosMenuNav import *
from Local.Libs.Global.Global import *
from TestCases.BootToLinuxShell                    import *
from TestCases.BootToBiosShell                     import *
from TestCases.BootToWindowsOS                     import *
from TestCases.FlashImage                          import *         
import os
import shutil
###############################################################################
# Variables
###############################################################################
global AutoTestLog
AutoTestLog = BATLogger
source_dir = "C:/Samples/"
###############################################################################
# Method definition
###############################################################################

class AutoTest:
  def main(SUT, TestCase, TestCaseExecResult):
    ImageType = AutoTest.GetFlashImageType(TestCase)
    SUT.TargetPduport.OFF()
    time.sleep(3)
    Status = eval("AutoTest."+ImageType)(SUT, TestCase, TestCaseExecResult)
    time.sleep(10)
    Status = AutoTest.ExecuteTest(SUT, TestCase, TestCaseExecResult)
    return Status

  def GetFlashImageType(TestCase):
    ImageType = TestCase["FlashImageType"]
    if "IFWI" == ImageType:
      return "IFWIImage"
    elif "BIOSROM" == ImageType:
      return "FlashBiosRom"
    else:
      TriageLog.error("Undefined Image Type")
      raise ValueError("Unacceptable value for 'FlashImageType' ")

  def IFWIImage(SUT, TestCase, TestCaseExecResult):
    try:
      VerifyFlash = TestCase["VerifyAfterFlash"]
    except:
      VerifyFlash = True
    CustomFolder = TestCase.get("CustomFolder")
    if CustomFolder is not None:
      IFWIImageFilePath = f"{SUT.MapNetworkDriveLetter}\\"+SUT.TargetExecu.get("Platform")+f"\\{CustomFolder}\\"
    else:
      IFWIImageFilePath = f"{SUT.MapNetworkDriveLetter}\\"+SUT.TargetExecu.get("Platform")+"\\Output\\"
    SUT.Flash = Flash(SUT.TargetExecu.get("FlashingTool"), SUT.TargetExecu.get("FlashingToolPath"), IFWIImageFilePath, TestCase["FlashImageType"], TestCase["FlashAddress"])
    Status = SUT.Flash.FlashRomImage(SUT.IfwiConfiguration, VerifyFlash=VerifyFlash)
    TestCaseExecResult.append(1)
    TestCaseExecResult.append(f"IFWI Config: {SUT.IfwiConfiguration}")
    return Status

  def FlashBiosRom(SUT, TestCase, TestCaseExecResult):
    try:
      VerifyFlash = TestCase["VerifyAfterFlash"]
    except:
      VerifyFlash = True
    IFWIImageFilePath = f"{SUT.MapNetworkDriveLetter}\\" + "\\Samples\\" + "\\CurrentExecution\\"
    SUT.Flash = Flash(SUT.TargetExecu.get("FlashingTool"), SUT.TargetExecu.get("FlashingToolPath"), IFWIImageFilePath, TestCase["FlashImageType"], TestCase["FlashAddress"])
    Status = SUT.Flash.FlashRomImage(SUT.IfwiConfiguration, VerifyFlash=VerifyFlash)
    TestCaseExecResult.append(1)
    TestCaseExecResult.append(f"ROM Config: {SUT.IfwiConfiguration}")
    return Status
  
  def ExecuteTest(SUT, TestCase, TestCaseExecResult):
    global Status
    Status = True
    Prompt = b''
    failcount = 0
    passcount = 0
    if TestCase["BoottoLinuxShell"] == "Yes":
        Status = BootToLinuxShell.SetLinuxShellPrompt(SUT, TestCase, None)
        BiosStep = TestCase.get("LinuxBIOSSettings")
        SUT.SerPort.SerialSend("reboot")
        SUT.SerPort.SendSerPortEnterKey()
        SUT.BiosMenuNav.WaitUntilF2PromptAppear(SendF2Key=True)
        SUT.BiosMenuNav.BiosVerify()
        SUT.BiosMenuNav.BiosDefaultSettings()
        SUT.BiosMenuNav.DynamicNavHandle.BiosChangeFromJson(TestCase.get("LinuxBIOSSettings"))   
        SUT.BiosMenuNav.BiosSaveChanges()
        SUT.BiosMenuNav.BiosReturnToMain()
        SUT.BiosMenuNav.BiosReset()    
        SUT.SerPort.SerialFlushComBuffer()
        Prompt, Status = SUT.SerPortLogin.LoginToLinuxOsShellPrompt()
        for i in range(int(TestCase["LinuxNumberofCommands"])):
          LinuxOutput = SUT.LinuxShellCommand.Shell((TestCase["LinuxCommand"][i]),StripNewSpace=True)
          for Result in LinuxOutput:
            if TestCase["LinuxKeywordUnwanted"][i] in Result:
              AutoTestLog.info("TEST FAILED") 
              Status = False
              failcount += 1
              break      
            if failcount == 0:
              AutoTestLog.info("TEST PASSED")  
              Status = True 
        for i in range(int(TestCase["LinuxNumberofCommands"])):
          LinuxOutput = SUT.LinuxShellCommand.Shell((TestCase["LinuxCommand"][i]),StripNewSpace=True)
          for Result in LinuxOutput:
            if TestCase["LinuxKeywordWanted"][i] in Result:
              AutoTestLog.info("TEST PASSED") 
              Status = True
              passcount += 1
              break      
            if passcount == 0:
              Status = False
              AutoTestLog.info("TEST FAILED")   
    
    failcount=0
    passcount=0

    if TestCase["BoottoEfiShell"] == "Yes":
        Status = BootToLinuxShell.SetLinuxShellPrompt(SUT, TestCase, None)
        BiosStep = TestCase.get("EfiShellBiosSettings")
        SUT.SerPort.SerialSend("reboot")
        SUT.SerPort.SendSerPortEnterKey()
        SUT.BiosMenuNav.WaitUntilF2PromptAppear(SendF2Key=True)
        SUT.BiosMenuNav.BiosVerify()
        SUT.BiosMenuNav.BiosDefaultSettings()
        SUT.BiosMenuNav.DynamicNavHandle.BiosChangeFromJson(TestCase.get("EfiShellBiosSettings"))   
        SUT.BiosMenuNav.BiosSaveChanges()
        SUT.BiosMenuNav.BiosReturnToMain()
        SUT.BiosMenuNav.BiosReset()    
        SUT.SerPort.SerialFlushComBuffer()
        Prompt, Status = SUT.SerPortLogin.LoginToLinuxOsShellPrompt()
        for i in range(int(TestCase["EFiShellNumberofCommands"])):
          LinuxOutput = SUT.LinuxShellCommand.Shell((TestCase["LinuxCommand"][i]),StripNewSpace=True)
          for Result in LinuxOutput:
            if TestCase["EfiShellKeywordUnWanted"][i] in Result:
              AutoTestLog.info("TEST FAILED") 
              Status = False
              failcount += 1
              break      
            if failcount == 0:
              AutoTestLog.info("TEST PASSED")   
              Status = True
        for i in range(int(TestCase["EFiShellNumberofCommands"])):
          LinuxOutput = SUT.LinuxShellCommand.Shell((TestCase["EfiShellCommand"][i]),StripNewSpace=True)
          for Result in LinuxOutput:
            if TestCase["EfiShellKeywordWanted"][i] in Result:
              AutoTestLog.info("TEST PASSED") 
              Status =  True
              passcount += 1
              break      
            if passcount == 0:
              AutoTestLog.info("TEST FAILED")  
              Status = False 

    if TestCase["BoottoWindowsOS"] == "Yes":
      Status = BootToWindowsOS.SetWindowsBootOrder(SUT, TestCase, TestCaseExecResult)

    #Use the below BAT test for mainly Windows OS testcases. However it can be used for Linux/EfiShell testcases as well.

    BATTest = TestCase["BAT Testcase"] 
    exec(f"from TestCases.{BATTest} import *")   
    Status = eval(BATTest+"."+"main")(SUT, TestCase, TestCaseExecResult)
    
    return Status