---
id: ue.cpp_extension
title: C++ and engine extension in Unreal Engine
domain: software_unreal_engine
tags: [cpp, modules, build-cs, target-cs, uclass, uproperty, ufunction, ubt, uht, slate, editor-extension, plugins, live-coding, visual-studio, rider, linux, macos]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Unreal Engine 5.8. Module and macro system stable since UE4; Visual Studio 2026 is the documented Windows compiler for 5.8."
sources:
  - {title: "Unreal Engine Modules", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-modules", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Objects in Unreal Engine", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/objects-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Hardware and Software Specifications", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/hardware-and-software-specifications-for-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Plugins", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/plugins-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
related: [ue.core_concepts, ue.blueprints, ue.python_automation]
---

# C++ and engine extension in Unreal Engine

**Summary.** An archviz practice can go a long way on Blueprint and Python. C++ becomes necessary when you need a reusable framework class, editor tooling that must run headless, or performance in a tight loop. This file covers the module system and `Build.cs`, the reflection macros, creating Actors and Components, editor extensions and Slate, plugin structure, Live Coding, and the practical toolchain on Windows, macOS and Linux.

## Key facts

| Item | Value |
|---|---|
| Build system | Unreal Build Tool (UBT), driven by `*.Target.cs` and `*.Build.cs` — **not** by the IDE solution |
| Reflection generator | Unreal Header Tool (UHT), runs before the C++ compiler |
| Windows compiler (5.8) | **Visual Studio 2026** for general development; VS 2022 for Nintendo and AGDE below v26.1.102 |
| Supported IDEs | Visual Studio (recommended), VS Code, JetBrains Rider |
| Module folder layout | `[ModuleName]/Private/`, `[ModuleName]/Public/`, `[ModuleName].Build.cs` |
| Module implementation macro | `IMPLEMENT_MODULE(FDefaultModuleImpl, ModuleName);` |
| Common module types | `Runtime`, `Editor` (see `EHostType::Type`) |
| Common loading phases | `Default`, `PreDefault` (see `ELoadingPhase::Type`) |
| Distributed build | Unreal Build Accelerator (UBA), recommended by Epic |
| Local compile baseline | 12–16 cores without a distributed build solution |
| C++ 20 modules | **Unrelated** to Unreal modules |

## Modules

A module encapsulates editor tools, runtime features, libraries or other functionality in a standalone unit of code. Every project and plugin has a primary module; you can define more to organise your code. Epic's stated benefits: code separation and encapsulation, separate compilation units (only changed modules recompile), an explicit dependency graph with Include-What-You-Use header discipline, controllable load/unload timing, and conditional inclusion by platform.

### Setting one up

1. Create a directory named after the module at the top level of `Source/` (subdirectories at any depth are allowed, which lets you group modules).
2. Create `[ModuleName].Build.cs` in its root.
3. Create `Private/` and `Public/` subfolders.
4. Create `Private/[ModuleName]Module.cpp`.
5. Add configuration for the module to the `.uproject` or `.uplugin`.
6. List the module as a dependency in the `Build.cs` of anything that uses it.
7. Regenerate IDE project files whenever you change a `Build.cs` or move source files — run `GenerateProjectFiles.bat`, right-click the `.uproject` → *Generate Project Files*, or use `File > Refresh Visual Studio Project` in the editor.

### `Build.cs`

```csharp
using UnrealBuildTool;

public class OkongoViz : ModuleRules
{
    public OkongoViz(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core", "CoreUObject", "Engine", "InputCore"
        });

        PrivateDependencyModuleNames.AddRange(new string[]
        {
            "Slate", "SlateCore", "UMG", "RenderCore",
            "CinematicCamera", "MovieScene", "LevelSequence"
        });

        if (Target.bBuildEditor)
        {
            PrivateDependencyModuleNames.AddRange(new string[]
            {
                "UnrealEd", "EditorScriptingUtilities",
                "EditorSubsystem", "AssetTools", "Blutility"
            });
        }
    }
}
```

Epic's rule for the two lists: put a module in **`PublicDependencyModuleNames`** if you use its classes in a *public* header, so that modules depending on yours can include your headers without error. Put it in **`PrivateDependencyModuleNames`** if it is used only in `.cpp` files. **Private dependencies are preferred wherever possible — they reduce compile times**, and forward declarations in headers let you make many dependencies private.

### Public and Private folders

These control the availability of the module's code to *other modules*, and have nothing to do with C++ access specifiers (which apply as normal on top).

- All `.cpp` files go in `Private/`.
- A header in `Private/` is not exposed outside the owning module.
- A header in `Public/` is exposed to any module that depends on yours; outside classes can extend those classes and declare variables of those types.
- A module at the end of the dependency chain (your game's primary module) does not need the folders at all — code outside them behaves as private.
- Mirror the folder structure: for every subfolder in `Public/`, create one of the same name in `Private/`. The editor's New Class Wizard maintains this automatically.

### Implementing the module

```cpp
// Private/OkongoVizModule.cpp
#include "Modules/ModuleManager.h"

IMPLEMENT_MODULE(FDefaultModuleImpl, OkongoViz);
```

`FDefaultModuleImpl` is an empty class extending `IModuleInterface`. Write your own class implementing `StartupModule()` and `ShutdownModule()` when you need registration work at load time — registering editor menu extensions, custom asset types, or detail customisations.

### Load control in `.uproject` / `.uplugin`

```json
"Modules": [
  {
    "Name": "OkongoViz",
    "Type": "Runtime",
    "LoadingPhase": "Default"
  },
  {
    "Name": "OkongoVizEditor",
    "Type": "Editor",
    "LoadingPhase": "PostEngineInit"
  }
]
```

The two common types are `Runtime` (in-game classes) and `Editor` (editor-only). If `LoadingPhase` is omitted it defaults to `Default`. Epic's practical tip: **if the editor frequently fails to find C++ classes in a plugin, set that module's loading phase to `PreDefault`.**

Further parameters: `IncludelistPlatforms` / `ExcludelistPlatforms` (`Win32`, `Win64`, `Mac`, `Linux`, `Android`, `IOS`), `IncludelistTargets` / `ExcludelistTargets` (`Game`, `Server`, `Client`, `Editor`, `Program`), `IncludelistTargetConfigurations` / `ExcludelistTargetConfigurations` (`Debug`, `DebugGame`, `Development`, `Shipping`, `Test`), and `IncludelistPrograms` / `ExcludelistPrograms`. `AdditionalDependencies` exists but Epic says to specify dependencies in `Build.cs` instead.

**Loading order within a phase is not deterministic.** If module A must be loaded before module B's `StartupModule`, call `FModuleManager::LoadModule` / `LoadModuleChecked` explicitly. Use `GetModule` when the module may or may not be present, such as during `ShutdownModule`.

UBT only compiles modules that appear in your project's dependency chain — an unreferenced module is simply skipped.

## The reflection macros

```cpp
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ArchvizRoom.generated.h"

UENUM(BlueprintType)
enum class ERoomType : uint8
{
    Living   UMETA(DisplayName = "Living"),
    Bedroom  UMETA(DisplayName = "Bedroom"),
    Kitchen  UMETA(DisplayName = "Kitchen"),
    Ablution UMETA(DisplayName = "Ablution")
};

USTRUCT(BlueprintType)
struct FRoomSpec
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room")
    ERoomType Type = ERoomType::Living;

    /** Finished floor area in square metres. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room",
              meta = (ClampMin = "0.0", UIMin = "0.0", UIMax = "200.0"))
    float FloorAreaM2 = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room")
    TSoftObjectPtr<UMaterialInterface> FloorFinish;
};

UCLASS(Blueprintable, BlueprintType,
       meta = (DisplayName = "Archviz Room"))
class OKONGOVIZ_API AArchvizRoom : public AActor
{
    GENERATED_BODY()

public:
    AArchvizRoom();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    TObjectPtr<USceneComponent> Root;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    TObjectPtr<UStaticMeshComponent> FloorMesh;

    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category = "Room")
    FRoomSpec Spec;

    /** Returns the room's area, computed from the floor mesh bounds. */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Room")
    float GetMeasuredAreaM2() const;

    /** Implemented in Blueprint; called when a visitor enters. */
    UFUNCTION(BlueprintImplementableEvent, Category = "Room")
    void OnVisitorEntered();

    /** Has a C++ default that Blueprint may override. */
    UFUNCTION(BlueprintNativeEvent, Category = "Room")
    void ApplyFinish(UMaterialInterface* Finish);
    virtual void ApplyFinish_Implementation(UMaterialInterface* Finish);

protected:
    virtual void BeginPlay() override;
    virtual void OnConstruction(const FTransform& Transform) override;
};
```

The specifiers you will use constantly:

| Specifier | Effect |
|---|---|
| `UCLASS(Blueprintable)` | Blueprints can derive from this class |
| `UCLASS(BlueprintType)` | The type can be used as a variable in Blueprint |
| `UCLASS(Abstract)` | Cannot be instantiated directly |
| `UPROPERTY(EditAnywhere)` | Editable on the archetype and on instances |
| `UPROPERTY(EditDefaultsOnly)` | Editable only on the class defaults |
| `UPROPERTY(EditInstanceOnly)` | Editable only on placed instances |
| `UPROPERTY(VisibleAnywhere)` | Shown but not editable |
| `UPROPERTY(BlueprintReadWrite / BlueprintReadOnly)` | Blueprint access |
| `UPROPERTY(Transient)` | Not serialised |
| `UPROPERTY(Replicated)` | Network replicated |
| `UPROPERTY(meta = (ClampMin, ClampMax, UIMin, UIMax, EditCondition))` | Details-panel behaviour |
| `UFUNCTION(BlueprintCallable)` | Callable from Blueprint **and from Python** |
| `UFUNCTION(BlueprintPure)` | No exec pins; must be side-effect free |
| `UFUNCTION(BlueprintImplementableEvent)` | Declared in C++, implemented only in Blueprint |
| `UFUNCTION(BlueprintNativeEvent)` | C++ default in `_Implementation`, overridable in Blueprint |
| `UFUNCTION(CallInEditor)` | Adds a button to the details panel |
| `UFUNCTION(Exec)` | Callable as a console command |

The critical consequence for this domain: **`BlueprintCallable` is also `Python`-callable**. Anything you expose to Blueprint immediately appears in the `unreal` module and can be invoked over Remote Control and by an MCP toolset. Designing the C++ surface *as an automation API* costs nothing extra.

Modern pointer discipline: use `TObjectPtr<T>` for `UPROPERTY` object references (not raw `T*`), `TSoftObjectPtr<T>` / `TSoftClassPtr<T>` for assets you want loaded on demand, and `TWeakObjectPtr<T>` for non-owning references. And remember the `UObject` rules from file `01`: no constructor arguments, lightweight constructors, `NewObject<T>()` and `CreateDefaultSubobject<T>()`, never `new`/`delete`.

```cpp
AArchvizRoom::AArchvizRoom()
{
    PrimaryActorTick.bCanEverTick = false;   // default to off

    Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);

    FloorMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("FloorMesh"));
    FloorMesh->SetupAttachment(Root);
}
```

## Custom components and subsystems

An **Actor Component** is the right unit for reusable behaviour. For archviz: a `UInteractableComponent` implementing focus/interact, a `UMeasurementComponent`, a `UFinishSwapComponent` that owns the Dynamic Material Instances for one Actor.

For global logic prefer a **subsystem** over a singleton Actor:

```cpp
UCLASS()
class OKONGOVIZ_API UConfiguratorSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    UFUNCTION(BlueprintCallable, Category = "Configurator")
    void SetOption(FName OptionId, FName ValueId);

    UPROPERTY(BlueprintAssignable, Category = "Configurator")
    FOnConfigurationChanged OnConfigurationChanged;
};
```

`UEditorSubsystem` is the editor-side equivalent, and is exactly the shape Epic's own `EditorActorSubsystem` and `LevelEditorSubsystem` take — which means your editor subsystem's `BlueprintCallable` functions are reachable from Python with `unreal.get_editor_subsystem(unreal.YourSubsystem)`. This is the single cleanest way to give an agent a project-specific API.

## Editor extensions and Slate

**Slate** is Unreal's own declarative C++ UI framework; the editor is built in it. **UMG** is a Blueprint-friendly layer over Slate for game UI. Editor tools are Slate.

Slate's declarative syntax:

```cpp
TSharedRef<SWidget> FArchvizToolsPanel::Construct()
{
    return SNew(SVerticalBox)
        + SVerticalBox::Slot().AutoHeight().Padding(4.f)
        [
            SNew(STextBlock)
            .Text(NSLOCTEXT("Archviz", "Title", "Okongo Visualisation Tools"))
            .Font(FCoreStyle::GetDefaultFontStyle("Bold", 12))
        ]
        + SVerticalBox::Slot().AutoHeight().Padding(4.f)
        [
            SNew(SButton)
            .Text(NSLOCTEXT("Archviz", "Nanite", "Enable Nanite on Selection"))
            .OnClicked(FOnClicked::CreateRaw(this, &FArchvizToolsPanel::OnEnableNanite))
        ];
}
```

Slate concepts to know: `SNew`/`SAssignNew`, `TSharedRef`/`TSharedPtr`, slots and `+ SVerticalBox::Slot()`, attributes bound with `TAttribute` and `_Lambda` delegates, and `FSlateStyleSet` for theming. Slate has no garbage collection — it uses shared pointers — and its widgets are not `UObject`s.

Common editor extension points, all registered from a module's `StartupModule()`:

- **Menus and toolbars** — `UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Tools")`
- **Custom tab spawners** — `FGlobalTabmanager::Get()->RegisterNomadTabSpawner(...)`
- **Details panel customisation** — `IDetailCustomization` / `IPropertyTypeCustomization`, registered with `FPropertyEditorModule`
- **Custom asset types** — `IAssetTypeActions` plus a `UFactory`
- **Asset actions** — `UAssetActionUtility` (a Blutility base class) gives right-click actions in the Content Browser with far less code
- **Commandlets** — `UCommandlet` subclasses, run with `-run=MyCommandlet`

**Be honest about the trade-off:** for an archviz practice, an **Editor Utility Widget calling Python** (file `06`) achieves most of what a Slate panel would, in a fraction of the time, with no compile step. Write Slate only when you need something UMG genuinely cannot do — a custom viewport, a graph editor, a property-type customisation.

## Plugins

A plugin is a self-contained folder with a `.uplugin` descriptor, optional `Source/` modules, optional `Content/`, and optional `Resources/`.

```
Plugins/
  OkongoTools/
    OkongoTools.uplugin
    Resources/Icon128.png
    Content/
      Python/                # auto-added to sys.path
      Blueprints/
    Source/
      OkongoTools/
        Private/
        Public/
        OkongoTools.Build.cs
```

```json
{
  "FileVersion": 3,
  "FriendlyName": "Okongo Tools",
  "Description": "Archviz automation for the Okongo residential project.",
  "Category": "Archviz",
  "CanContainContent": true,
  "Installed": false,
  "Modules": [
    { "Name": "OkongoTools", "Type": "Editor", "LoadingPhase": "PostEngineInit" }
  ],
  "Plugins": [
    { "Name": "PythonScriptPlugin", "Enabled": true },
    { "Name": "EditorScriptingUtilities", "Enabled": true }
  ]
}
```

**Project plugins** live in `<Project>/Plugins/` and travel with the project. **Engine plugins** live in `<Engine>/Plugins/` and are shared by every project on that engine. For a practice standardising a workflow across jobs, a project plugin copied per project is easier to version than an engine plugin, but an engine plugin avoids drift. Pick one and be consistent.

A plugin's `Content/Python/` is auto-added to `sys.path`, and a plugin can ship an `init_unreal.py`. That combination — a plugin containing Python toolsets, Editor Utility Widgets and a small C++ editor subsystem — is the natural home for a practice's archviz automation, and is exactly the shape Epic's own `ToolsetRegistry` plugin takes.

## Live Coding

Live Coding (Ctrl+Alt+F11 by default, or the toolbar's Compile button) patches changed C++ into the running editor without a restart.

What it handles: function body changes, most implementation edits.

What it does **not** handle, requiring a full editor restart:

- Adding, removing or changing `UPROPERTY` / `UFUNCTION` declarations
- Adding new `UCLASS`, `USTRUCT` or `UENUM` types
- Changing class layout or inheritance
- Changing `Build.cs` files

Epic states this explicitly for MCP toolsets: *Live Coding does not propagate new `UFUNCTION` declarations; adding a Tool requires an editor restart.* The same rule applies everywhere.

Working practice: iterate on implementation with Live Coding; batch header changes and take one restart. Live Coding accumulates patches, and a long session of them eventually destabilises the editor — restart every hour or so of heavy work.

## Toolchain by platform

**Windows** — the primary and only fully-featured archviz platform.
- Visual Studio 2026 (VS 2022 for Nintendo and AGDE below v26.1.102). Install the *Game development with C++* workload plus the *Unreal Engine installer* component and *.NET desktop development*.
- VS Code and Rider are supported alternatives. Rider for Unreal Engine is materially better at Unreal-aware navigation and refactoring; many teams use it in preference to Visual Studio.
- Prerequisite installers ship with the engine at `Engine/Extras/Redist/en-us` — needed if you build from source or prepare a machine manually (for example a Swarm Agent).
- Enable **Unreal Build Accelerator (UBA)** for distributed compilation; without a distributed solution, 12–16 cores is the practical baseline.

**macOS** — Xcode with the command-line tools. The engine runs and C++ builds, but Datasmith importers do not exist on macOS, Nanite and Lumen on Metal have historically lagged the D3D12 path, and most Datasmith exporter plugins are Windows-only (the exceptions being SketchUp Pro, Archicad and Rhino). Usable for asset and Blueprint work; not the machine you render on.

**Linux** — clang toolchain, cross-compilation supported from Windows. Genuinely useful for headless render nodes and CI: `UnrealEditor-Cmd` with `-run=pythonscript` and `-NullRHI` runs fine, and Movie Render Queue works with a GPU present. Not a desktop authoring platform for archviz.

## When to write C++ — and when not to

Write C++ when:

1. You need a **base class** several Blueprints derive from, with `BlueprintImplementableEvent` hooks. This is Epic's recommended division of labour and it works well.
2. You need **editor tooling that must run headless** and cannot be expressed in Python.
3. You have a **genuine hot loop** — procedural geometry, mesh analysis, thousands of per-frame operations.
4. You need engine functionality **not exposed to Blueprint** — and therefore not to Python either.
5. You want the logic **diffable and mergeable in source control**. `.uasset` Blueprints are not.

Do not write C++ because it feels more professional. For an archviz practice the compile dependency, the build times and the hiring constraint are real costs, and the failure mode — a half-finished C++ framework nobody but its author can extend — is worse than a slightly ugly Blueprint. **Python for editor automation, Blueprint for runtime interactivity, C++ only where those two genuinely cannot reach.**

## Open questions

- Whether `PCHUsageMode.UseExplicitOrSharedPCHs` remains the recommended default in 5.8 was not verified on the pages fetched.
- The Live Coding default keyboard shortcut (Ctrl+Alt+F11) was not verified against 5.8 documentation — **needs verification**.

## Sources

- [Unreal Engine Modules](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-modules) — Epic Games, accessed 2026-08-25
- [Objects in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/objects-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Unreal Object Handling](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-object-handling-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Plugins](https://dev.epicgames.com/documentation/en-us/unreal-engine/plugins-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Hardware and Software Specifications](https://dev.epicgames.com/documentation/en-us/unreal-engine/hardware-and-software-specifications-for-unreal-engine) — Epic Games, accessed 2026-08-25
- [Unreal MCP](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor) — Epic Games, accessed 2026-08-25 (Live Coding / `UFUNCTION` limitation)
- [Creating User Interfaces with UMG and Slate](https://dev.epicgames.com/documentation/en-us/unreal-engine/creating-user-interfaces-with-umg-and-slate-in-unreal-engine) — Epic Games, accessed 2026-08-25

