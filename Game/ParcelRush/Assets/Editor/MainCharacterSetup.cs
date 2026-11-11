using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UnityEngine;

// Step 6: puts the rigged Blender character (MainCharacter.fbx) into the game.
// Menu: Parcel Rush > Set Up Main Character. Safe to run again after re-exporting the FBX.
public static class MainCharacterSetup
{
    const string Folder = "Assets/Characters/MainCharacter";
    const string FbxPath = Folder + "/MainCharacter.fbx";
    const string ControllerPath = Folder + "/MainCharacter.controller";
    const string ScenePath = "Assets/Scenes/MainCity.unity";
    const float WalkAnimationSpeed = 1.12f;   // m/s, from animate_main_character.py

    [MenuItem("Parcel Rush/Set Up Main Character")]
    public static void SetUp()
    {
        Avatar avatar = ConfigureImport();
        AnimatorController controller = CreateController();
        PutInScene(avatar, controller);
        Debug.Log("Main character set up. Press Play and walk with WASD / arrow keys.");
    }

    // 1. Rig tab = Humanoid, Animation tab = Loop Time + Loop Pose, root motion baked into pose
    static Avatar ConfigureImport()
    {
        var importer = AssetImporter.GetAtPath(FbxPath) as ModelImporter;
        if (importer == null)
            throw new System.Exception("Missing " + FbxPath + " - export it from Blender first.");

        importer.animationType = ModelImporterAnimationType.Human;
        importer.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
        importer.importAnimation = true;
        importer.SaveAndReimport();

        // Unity's automap finds the body bones but not the fingers, so map those by name.
        // The skeleton list is rebuilt from the FBX so newly added bones (like fingers) are always in it.
        var description = importer.humanDescription;
        description.human = WithFingers(description.human);
        var model = AssetDatabase.LoadAssetAtPath<GameObject>(FbxPath);
        description.skeleton = model.GetComponentsInChildren<Transform>(true)
            .Select(t => new SkeletonBone { name = t.name, position = t.localPosition, rotation = t.localRotation, scale = t.localScale })
            .ToArray();
        importer.humanDescription = description;
        importer.SaveAndReimport();            // the clip list is only complete once the avatar is valid

        var clips = importer.defaultClipAnimations
            .Where(c => c.takeName.Contains("Walk") || c.takeName.Contains("Idle"))
            .ToArray();
        foreach (var clip in clips)
        {
            clip.name = clip.takeName.Contains("Walk") ? "Walk" : "Idle";
            clip.loopTime = true;
            clip.loopPose = true;
            clip.lockRootRotation = true;      clip.keepOriginalOrientation = true;
            clip.lockRootHeightY = true;       clip.keepOriginalPositionY = true;
            clip.lockRootPositionXZ = true;    clip.keepOriginalPositionXZ = true;
        }
        importer.clipAnimations = clips;
        importer.SaveAndReimport();

        Avatar avatar = AssetDatabase.LoadAllAssetsAtPath(FbxPath).OfType<Avatar>().FirstOrDefault();
        if (avatar == null || !avatar.isValid || !avatar.isHuman)
            throw new System.Exception("Humanoid avatar is not valid - open the FBX Rig tab > Configure to check the bone mapping.");
        return avatar;
    }

    static readonly string[] FingerNames = { "Thumb", "Index", "Middle", "Ring", "Little" };
    static readonly string[] Phalanges = { "Proximal", "Intermediate", "Distal" };

    // Blender bones thumb.01.L .. pinky.03.R  ->  Unity "Left Thumb Proximal" .. "Right Little Distal"
    static HumanBone[] WithFingers(HumanBone[] mapped)
    {
        var bones = mapped.Where(b => !FingerNames.Any(f => b.humanName.Contains(f))).ToList();
        foreach (var side in new[] { "Left", "Right" })
        {
            for (int f = 0; f < FingerNames.Length; f++)
            {
                for (int p = 0; p < Phalanges.Length; p++)
                {
                    string blenderName = (f == 4 ? "pinky" : FingerNames[f].ToLower()) + ".0" + (p + 1) + "." + side[0];
                    bones.Add(new HumanBone
                    {
                        humanName = side + " " + FingerNames[f] + " " + Phalanges[p],
                        boneName = blenderName,
                        limit = new HumanLimit { useDefaultValues = true },
                    });
                }
            }
        }
        return bones.ToArray();
    }

    static AnimationClip Clip(string name)
    {
        var clip = AssetDatabase.LoadAllAssetsAtPath(FbxPath).OfType<AnimationClip>()
            .FirstOrDefault(c => c.name == name);
        if (clip == null) throw new System.Exception("No '" + name + "' clip in " + FbxPath);
        return clip;
    }

    // 2. Animator Controller: Idle <-> Walk using the Speed parameter
    static AnimatorController CreateController()
    {
        AssetDatabase.DeleteAsset(ControllerPath);
        var controller = AnimatorController.CreateAnimatorControllerAtPath(ControllerPath);
        controller.AddParameter("Speed", AnimatorControllerParameterType.Float);
        controller.AddParameter("MotionSpeed", AnimatorControllerParameterType.Float);
        var parameters = controller.parameters;
        parameters[1].defaultFloat = 1f;
        controller.parameters = parameters;

        var sm = controller.layers[0].stateMachine;
        var idle = sm.AddState("Idle", new Vector3(300, 0, 0));
        idle.motion = Clip("Idle");
        var walk = sm.AddState("Walk", new Vector3(300, 100, 0));
        walk.motion = Clip("Walk");
        walk.speedParameterActive = true;
        walk.speedParameter = "MotionSpeed";
        sm.defaultState = idle;

        var toWalk = idle.AddTransition(walk);
        toWalk.hasExitTime = false;
        toWalk.duration = 0.15f;
        toWalk.AddCondition(AnimatorConditionMode.Greater, 0.1f, "Speed");

        var toIdle = walk.AddTransition(idle);
        toIdle.hasExitTime = false;
        toIdle.duration = 0.2f;
        toIdle.AddCondition(AnimatorConditionMode.Less, 0.1f, "Speed");

        EditorUtility.SetDirty(controller);
        AssetDatabase.SaveAssets();
        return controller;
    }

    // 3. Swap the capsule placeholder for the real character in MainCity
    static void PutInScene(Avatar avatar, AnimatorController controller)
    {
        var scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        var courier = GameObject.Find("Courier");
        if (courier == null) throw new System.Exception("No 'Courier' object in " + ScenePath);

        var capsuleRenderer = courier.GetComponent<MeshRenderer>();
        if (capsuleRenderer != null) capsuleRenderer.enabled = false;           // hide the capsule
        var placeholderBag = courier.transform.Find("ParcelBackpack");
        if (placeholderBag != null) placeholderBag.gameObject.SetActive(false);  // cube backpack, kept but hidden

        var old = courier.transform.Find("MainCharacter");
        if (old != null) Object.DestroyImmediate(old.gameObject);

        // pivot at the feet: controller sized for a 1.75 m character
        var cc = courier.GetComponent<CharacterController>();
        cc.height = 1.8f;
        cc.radius = 0.3f;
        cc.center = new Vector3(0f, cc.height / 2f + cc.skinWidth, 0f);
        var p = courier.transform.position;
        courier.transform.position = new Vector3(p.x, 0f, p.z);

        var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(FbxPath);
        var model = (GameObject)PrefabUtility.InstantiatePrefab(prefab, courier.transform);
        model.name = "MainCharacter";
        model.transform.localPosition = Vector3.zero;
        model.transform.localRotation = Quaternion.identity;

        var animator = model.GetComponent<Animator>();
        if (animator == null) animator = model.AddComponent<Animator>();
        animator.avatar = avatar;
        animator.runtimeAnimatorController = controller;
        animator.applyRootMotion = false;

        var move = courier.GetComponent<ThirdPersonCourierController>();
        if (move != null)
        {
            move.animator = animator;
            move.walkAnimationSpeed = WalkAnimationSpeed;
            move.walkSpeed = 1.35f;
            move.sprintSpeed = 2.2f;
            EditorUtility.SetDirty(move);
        }

        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
    }
}
