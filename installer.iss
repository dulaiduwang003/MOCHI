; star安装程序脚本 把dist\Star打成StarSetup.exe 先跑build.ps1

#define MyAppName "斯塔 Star"
; 版本号由build.ps1传入 这里是手动编译的兜底
#ifndef MyAppVersion
  #define MyAppVersion "0.1.0"
#endif
#define MyAppPublisher "bdth"
#define MyAppExeName "Star.exe"

[Setup]
; appid固定不要改
AppId={{8F3A1C5E-9B2D-4E7A-A1F6-2C9D4B8E7A30}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
; 默认装用户目录免UAC
DefaultDirName={autopf}\Star
DefaultGroupName=Star
DisableDirPage=no
DisableProgramGroupPage=yes
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=StarSetup
SetupIconFile=star.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64

[Languages]
; 默认英文向导 要中文把ChineseSimplified.isl放进Languages目录再开下面那行
Name: "en"; MessagesFile: "compiler:Default.isl"
; Name: "chs"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startup"; Description: "Start Star automatically when I sign in (开机自启)"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
; 整个pyinstaller目录一起装
Source: "dist\Star\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startup

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

; 卸载只删程序 用户数据留在appdata
