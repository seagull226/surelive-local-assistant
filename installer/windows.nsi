Unicode True
!include "MUI2.nsh"
!include "StrFunc.nsh"
!include "LogicLib.nsh"
${StrRep}
Name "SureLive 本机字幕助手（隔离试用）"
OutFile "${ROOT}\SureLive-ASR-Setup-Preview.exe"
InstallDir "$LOCALAPPDATA\Programs\SureLive-ASR-Preview"
RequestExecutionLevel user
SetCompressor zlib
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"
Section "Helper"
 SetOutPath "$INSTDIR"
 File /r "${ROOT}\payload\*"
 nsExec::ExecToLog '$\"$INSTDIR\SureLive-NativeHost.exe$\" --write-manifest'
 Pop $0
 ${If} $0 != 0
  Abort "助手注册失败，请重试安装。"
 ${EndIf}
 WriteRegStr HKCU "Software\Google\Chrome\NativeMessagingHosts\com.surelive.asr.preview" "" "$INSTDIR\native-host.json"
 WriteRegStr HKCU "Software\Microsoft\Edge\NativeMessagingHosts\com.surelive.asr.preview" "" "$INSTDIR\native-host.json"
 SetRegView 64
 WriteRegStr HKCU "Software\Google\Chrome\NativeMessagingHosts\com.surelive.asr.preview" "" "$INSTDIR\native-host.json"
 WriteRegStr HKCU "Software\Microsoft\Edge\NativeMessagingHosts\com.surelive.asr.preview" "" "$INSTDIR\native-host.json"
 SetRegView 32
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SureLive-ASR-Preview" "DisplayName" "SureLive 本机字幕助手（隔离试用）"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SureLive-ASR-Preview" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
 WriteUninstaller "$INSTDIR\Uninstall.exe"
 CreateDirectory "$SMPROGRAMS\SureLive ASR Preview"
 CreateShortcut "$SMPROGRAMS\SureLive ASR Preview\本机字幕助手.lnk" "$INSTDIR\SureLive-ASR-Helper.exe"
SectionEnd
Section "Uninstall"
 SetRegView 64
 ReadRegStr $0 HKCU "Software\Microsoft\Edge\NativeMessagingHosts\com.surelive.asr.preview" ""
 ${If} $0 == "$INSTDIR\native-host.json"
  DeleteRegKey HKCU "Software\Microsoft\Edge\NativeMessagingHosts\com.surelive.asr.preview"
 ${EndIf}
 ReadRegStr $0 HKCU "Software\Google\Chrome\NativeMessagingHosts\com.surelive.asr.preview" ""
 ${If} $0 == "$INSTDIR\native-host.json"
  DeleteRegKey HKCU "Software\Google\Chrome\NativeMessagingHosts\com.surelive.asr.preview"
 ${EndIf}
 SetRegView 32
 ReadRegStr $0 HKCU "Software\Microsoft\Edge\NativeMessagingHosts\com.surelive.asr.preview" ""
 ${If} $0 == "$INSTDIR\native-host.json"
  DeleteRegKey HKCU "Software\Microsoft\Edge\NativeMessagingHosts\com.surelive.asr.preview"
 ${EndIf}
 ReadRegStr $0 HKCU "Software\Google\Chrome\NativeMessagingHosts\com.surelive.asr.preview" ""
 ${If} $0 == "$INSTDIR\native-host.json"
  DeleteRegKey HKCU "Software\Google\Chrome\NativeMessagingHosts\com.surelive.asr.preview"
 ${EndIf}
 DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SureLive-ASR-Preview"
 Delete "$SMPROGRAMS\SureLive ASR Preview\本机字幕助手.lnk"
 RMDir "$SMPROGRAMS\SureLive ASR Preview"
 ; Delete only our installed file set, never recursively delete a user-selected directory.
 !include "${ROOT}\uninstall-files.nsh"
 Delete "$INSTDIR\native-host.json"
 Delete "$INSTDIR\Uninstall.exe"
 RMDir "$INSTDIR"
SectionEnd
