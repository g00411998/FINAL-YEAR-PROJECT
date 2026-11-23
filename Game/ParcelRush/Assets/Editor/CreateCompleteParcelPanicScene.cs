using TMPro;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;

/// <summary>
/// Makes a clean, separate play-scene copy from the currently open practice scene.
/// Existing scenes stay in place. The copy keeps the courier/UI, removes the hidden
/// backup objects, restores working pickup/delivery triggers, and adds a styled backdrop.
/// </summary>
public static class CreateCompleteParcelPanicScene
{
    private const string OutputPath = "Assets/Scenes/ParcelPanic_CompleteTown.unity";
    private const string MaterialsFolder = "Assets/Materials";

    [MenuItem("Tools/Parcel Panic/Expand Roads and Add Parked Cars")]
    private static void ExpandRoadsAndAddCars()
    {
        Transform town = GameObject.Find("TownLayout")?.transform;
        Transform world = GameObject.Find("Environment")?.transform;
        if (town == null || world == null)
        {
            EditorUtility.DisplayDialog("Open the combined town scene", "Open ParcelPanic_CompleteTown from Assets/Scenes, then run this command again.", "OK");
            return;
        }

        Material road = AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/Parcel Panic Blockout/Blockout_RoadGrey.mat");
        Material dash = AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/Parcel Panic Blockout/Blockout_RoadWhite.mat");
        Material[] carMaterials =
        {
            AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/Parcel Panic Blockout/Blockout_RoofBlue.mat"),
            AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/Parcel Panic Blockout/Blockout_DoorBrown.mat"),
            AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/Parcel Panic Blockout/Blockout_WindowCyan.mat"),
            AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/Parcel Panic Blockout/Blockout_Blue.mat")
        };

        Transform oldLinks = town.Find("ExtraStreetLinks");
        if (oldLinks != null) Object.DestroyImmediate(oldLinks.gameObject);
        Transform oldCars = world.Find("ParkedCarPlaceholders");
        if (oldCars != null) Object.DestroyImmediate(oldCars.gameObject);

        Transform links = MakeGroup("ExtraStreetLinks", town);
        CreateStreetLink("WestCrossTownLink", links, new Vector2(-15f, 12f), new Vector2(-15f, -12f), road, dash);
        CreateStreetLink("EastCrossTownLink", links, new Vector2(15f, 12f), new Vector2(15f, -12f), road, dash);

        Transform cars = MakeGroup("ParkedCarPlaceholders", world);
        CreateCar("ParkedCar_NorthWest", cars, new Vector3(-8f, 0f, 11.8f), 0f, carMaterials[0]);
        CreateCar("ParkedCar_SouthEast", cars, new Vector3(8f, 0f, -11.8f), 0f, carMaterials[1]);
        CreateCar("ParkedCar_West", cars, new Vector3(-12f, 0f, -5f), 90f, carMaterials[2]);
        CreateCar("ParkedCar_East", cars, new Vector3(12f, 0f, 5f), 90f, carMaterials[3]);

        Scene active = SceneManager.GetActiveScene();
        if (active.IsValid())
        {
            EditorSceneManager.MarkSceneDirty(active);
            EditorSceneManager.SaveScene(active);
        }
        Selection.activeGameObject = links.gameObject;
        Debug.Log("Added two connected cross-town streets and four non-blocking parked car placeholders.");
    }

    private static void CreateStreetLink(string name, Transform parent, Vector2 a, Vector2 b, Material road, Material dash)
    {
        Vector2 delta = b - a;
        float yaw = Mathf.Atan2(-delta.y, delta.x) * Mathf.Rad2Deg;
        Vector2 midpoint = (a + b) * 0.5f;
        GameObject segment = GameObject.CreatePrimitive(PrimitiveType.Cube);
        segment.name = name;
        segment.transform.SetParent(parent, false);
        segment.transform.position = new Vector3(midpoint.x, 0.06f, midpoint.y);
        segment.transform.localScale = new Vector3(delta.magnitude, 0.12f, 4.2f);
        segment.transform.rotation = Quaternion.Euler(0f, yaw, 0f);
        Renderer renderer = segment.GetComponent<Renderer>();
        if (renderer != null && road != null) renderer.sharedMaterial = road;

        int count = Mathf.Max(1, Mathf.FloorToInt(delta.magnitude / 3.5f) - 1);
        for (int i = 0; i < count; i++)
        {
            float t = (i + 1f) / (count + 1f);
            Vector2 point = Vector2.Lerp(a, b, t);
            GameObject marking = GameObject.CreatePrimitive(PrimitiveType.Cube);
            marking.name = "RoadDash";
            marking.transform.SetParent(parent, false);
            marking.transform.position = new Vector3(point.x, 0.14f, point.y);
            marking.transform.localScale = new Vector3(0.85f, 0.025f, 0.12f);
            marking.transform.rotation = Quaternion.Euler(0f, yaw, 0f);
            Collider markingCollider = marking.GetComponent<Collider>();
            if (markingCollider != null) markingCollider.enabled = false;
            Renderer markingRenderer = marking.GetComponent<Renderer>();
            if (markingRenderer != null && dash != null) markingRenderer.sharedMaterial = dash;
        }
    }

    private static void CreateCar(string name, Transform parent, Vector3 position, float yaw, Material paint)
    {
        Transform car = MakeGroup(name, parent);
        car.position = position;
        car.rotation = Quaternion.Euler(0f, yaw, 0f);
        CreateCarPart("Body", car, new Vector3(0f, 0.43f, 0f), new Vector3(2.8f, 0.62f, 1.45f), paint);
        CreateCarPart("Cabin", car, new Vector3(0f, 0.88f, 0f), new Vector3(1.45f, 0.52f, 1.12f), paint);
        Material tyre = AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/Parcel Panic Blockout/Blockout_RoadGrey.mat");
        for (int x = -1; x <= 1; x += 2)
        for (int z = -1; z <= 1; z += 2)
            CreateCarPart("Wheel", car, new Vector3(x * 0.88f, 0.2f, z * 0.53f), new Vector3(0.46f, 0.38f, 0.22f), tyre);
    }

    private static void CreateCarPart(string name, Transform parent, Vector3 localPosition, Vector3 size, Material material)
    {
        GameObject part = GameObject.CreatePrimitive(PrimitiveType.Cube);
        part.name = name;
        part.transform.SetParent(parent, false);
        part.transform.localPosition = localPosition;
        part.transform.localScale = size;
        Collider collider = part.GetComponent<Collider>();
        if (collider != null) collider.enabled = false;
        Renderer renderer = part.GetComponent<Renderer>();
        if (renderer != null && material != null) renderer.sharedMaterial = material;
    }

    [MenuItem("Tools/Parcel Panic/Polish Open Town Scene")]
    private static void PolishOpenScene()
    {
        // Keep the scene looking like a bright daytime prototype instead of a sunset.
        Material sky = RenderSettings.skybox;
        if (sky != null)
        {
            if (sky.HasProperty("_SkyTint")) sky.SetColor("_SkyTint", new Color(0.68f, 0.82f, 0.96f));
            if (sky.HasProperty("_GroundColor")) sky.SetColor("_GroundColor", new Color(0.47f, 0.61f, 0.68f));
            if (sky.HasProperty("_Exposure")) sky.SetFloat("_Exposure", 0.8f);
            if (sky.HasProperty("_AtmosphereThickness")) sky.SetFloat("_AtmosphereThickness", 0.75f);
            if (sky.HasProperty("_SunSize")) sky.SetFloat("_SunSize", 0.01f);
            EditorUtility.SetDirty(sky);
        }

        RenderSettings.sun = null;
        RenderSettings.fogColor = new Color(0.68f, 0.8f, 0.86f);

        TMP_Text leftoverTask = FindText("TaskText");
        if (leftoverTask != null)
            leftoverTask.gameObject.SetActive(false);

        Transform hills = GameObject.Find("DistantGreenHills")?.transform;
        if (hills != null)
        {
            foreach (Transform hill in hills)
            {
                hill.localScale = new Vector3(40f, 8f, 28f);
                Vector3 position = hill.position;
                hill.position = new Vector3(position.x, -5f, position.z);
            }
        }

        Scene active = SceneManager.GetActiveScene();
        if (active.IsValid())
        {
            EditorSceneManager.MarkSceneDirty(active);
            EditorSceneManager.SaveScene(active);
        }
        Debug.Log("Polished the active town scene: blue daytime sky, distant low hills, and no duplicate task label.");
    }

    [MenuItem("Tools/Parcel Panic/Create Complete Town Scene Copy")]
    private static void CreateCopy()
    {
        Scene source = SceneManager.GetActiveScene();
        if (!source.IsValid() || string.IsNullOrEmpty(source.path))
        {
            EditorUtility.DisplayDialog("Save the practice scene first", "Open your MainCity_Practice 1 scene from Assets/Scenes, then run this command again.", "OK");
            return;
        }

        string targetPath = AssetDatabase.LoadAssetAtPath<SceneAsset>(OutputPath) == null
            ? OutputPath
            : AssetDatabase.GenerateUniqueAssetPath("Assets/Scenes/ParcelPanic_CompleteTown.unity");

        bool savedCopy = EditorSceneManager.SaveScene(source, targetPath, true);
        if (!savedCopy)
        {
            EditorUtility.DisplayDialog("Could not create scene copy", "Unity could not save a copy of the currently open scene.", "OK");
            return;
        }

        AssetDatabase.Refresh();
        Scene combined = EditorSceneManager.OpenScene(targetPath, OpenSceneMode.Single);
        SceneManager.SetActiveScene(combined);

        GameObject temporaryBackup = GameObject.Find("Temporary");
        if (temporaryBackup != null)
            Object.DestroyImmediate(temporaryBackup);

        GameObject ground = GameObject.Find("Ground");
        GameObject town = GameObject.Find("Expanded_Town_Loop");
        GameObject courier = GameObject.Find("Courier");
        Camera mainCamera = Camera.main;
        if (mainCamera == null)
            mainCamera = Object.FindFirstObjectByType<Camera>();

        if (ground == null || town == null || courier == null || mainCamera == null)
        {
            EditorUtility.DisplayDialog("Scene pieces missing", "The opened practice scene needs Ground, Expanded_Town_Loop, Courier, and Main Camera objects. The source scene is untouched; check the new copy before using it.", "OK");
            return;
        }

        Transform environment = MakeGroup("Environment");
        Transform gameplay = MakeGroup("Gameplay");
        Transform uiRoot = MakeGroup("UI");
        Transform backdrop = MakeGroup("WorldBackdrop", environment);

        ParentKeepWorld(ground.transform, environment);
        ParentKeepWorld(town.transform, environment);
        town.name = "TownLayout";
        ParentKeepWorld(courier.transform, gameplay);

        Vector3 groundScale = ground.transform.localScale;
        ground.transform.localScale = new Vector3(50f, groundScale.y, 42f);
        ground.SetActive(true);
        Collider floorCollider = ground.GetComponent<Collider>();
        if (floorCollider != null)
        {
            floorCollider.enabled = true;
            floorCollider.isTrigger = false;
        }

        Material groundMaterial = AssetDatabase.LoadAssetAtPath<Material>(MaterialsFolder + "/Ground.mat");
        if (groundMaterial != null)
            SetMaterial(ground, groundMaterial);

        GameObject parcel = GameObject.Find("ParcelBackpack");
        if (parcel != null)
        {
            parcel.SetActive(false);
            Material parcelMaterial = AssetDatabase.LoadAssetAtPath<Material>(MaterialsFolder + "/ParcelBrown.mat");
            if (parcelMaterial != null) SetMaterial(parcel, parcelMaterial);
        }

        TMP_Text currentJob = FindText("CurrentJobText");
        TMP_Text score = FindText("ScoreText");
        TMP_Text timer = FindText("TimerText");
        TMP_Text complete = FindText("DeliveryCompleteText");
        TMP_Text leftoverTask = FindText("TaskText");
        if (leftoverTask != null)
            leftoverTask.gameObject.SetActive(false);
        CanvasGroup completeGroup = complete != null ? complete.GetComponentInParent<CanvasGroup>(true) : null;
        if (complete != null && completeGroup == null)
            completeGroup = complete.transform.parent.gameObject.AddComponent<CanvasGroup>();

        Canvas[] canvases = Object.FindObjectsByType<Canvas>(FindObjectsInactive.Include, FindObjectsSortMode.None);
        foreach (Canvas canvas in canvases)
        {
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.worldCamera = null;
            ParentKeepWorld(canvas.transform, uiRoot);
        }

        if (currentJob != null) currentJob.text = "CURRENT JOB\nGo to the yellow pickup point";
        if (score != null) score.text = "SCORE 000";
        if (timer != null) timer.text = "TIME 02:00";
        if (completeGroup != null)
        {
            completeGroup.alpha = 0f;
            completeGroup.gameObject.SetActive(false);
        }

        GameObject pickup = MakeMarker("PickupPoint", gameplay.transform, new Vector3(-20.5f, 0.4f, 17.2f), new Color(1f, 0.82f, 0.05f), MaterialsFolder + "/PickupPoint.mat");
        PickupPointTrigger pickupTrigger = pickup.AddComponent<PickupPointTrigger>();
        pickupTrigger.currentJobText = currentJob;
        pickupTrigger.parcelVisual = parcel;

        GameObject delivery = MakeMarker("DeliveryPoint", gameplay.transform, new Vector3(20.5f, 0.4f, -17.2f), new Color(0.55f, 0.12f, 0.95f), MaterialsFolder + "/DeliveryTestPoint.mat");
        DeliveryPointTrigger deliveryTrigger = delivery.AddComponent<DeliveryPointTrigger>();
        deliveryTrigger.currentJobText = currentJob;
        deliveryTrigger.scoreText = score;
        deliveryTrigger.timerText = timer;
        deliveryTrigger.deliveryCompleteText = complete;
        deliveryTrigger.deliveryCompleteGroup = completeGroup;

        courier.tag = "Player";
        courier.transform.position = new Vector3(-17f, 1.1f, 8f);

        ThirdPersonCamera cameraController = mainCamera.GetComponent<ThirdPersonCamera>();
        if (cameraController != null) cameraController.target = courier.transform;
        ThirdPersonCourierController courierController = courier.GetComponent<ThirdPersonCourierController>();
        if (courierController != null) courierController.cameraTransform = mainCamera.transform;

        ConfigureLightAndSky(mainCamera);
        AddBackdrop(backdrop, groundMaterial);
        EnsureEventSystem();

        EditorSceneManager.MarkSceneDirty(combined);
        EditorSceneManager.SaveScene(combined);
        Selection.activeGameObject = town;
        Debug.Log("Created and saved " + targetPath + ". Existing practice scenes were not changed.");
        EditorUtility.DisplayDialog("Complete town scene created", "The combined scene is open and saved as:\n" + targetPath + "\n\nYour original practice scenes are unchanged.", "OK");
    }

    private static Transform MakeGroup(string name, Transform parent = null)
    {
        GameObject group = new GameObject(name);
        if (parent != null) group.transform.SetParent(parent, false);
        return group.transform;
    }

    private static void ParentKeepWorld(Transform item, Transform parent)
    {
        if (item != null) item.SetParent(parent, true);
    }

    private static TMP_Text FindText(string objectName)
    {
        GameObject found = GameObject.Find(objectName);
        return found != null ? found.GetComponent<TMP_Text>() : null;
    }

    private static GameObject MakeMarker(string name, Transform parent, Vector3 position, Color fallbackColor, string materialPath)
    {
        GameObject marker = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        marker.name = name;
        marker.transform.SetParent(parent, false);
        marker.transform.position = position;
        marker.transform.localScale = new Vector3(1.1f, 0.4f, 1.1f);
        Collider collider = marker.GetComponent<Collider>();
        collider.isTrigger = true;
        collider.enabled = true;

        Material material = AssetDatabase.LoadAssetAtPath<Material>(materialPath);
        if (material == null)
        {
            Shader shader = Shader.Find("Standard");
            material = new Material(shader) { name = name + "_GeneratedMaterial", color = fallbackColor };
        }
        SetMaterial(marker, material);
        return marker;
    }

    private static void SetMaterial(GameObject obj, Material material)
    {
        Renderer renderer = obj.GetComponent<Renderer>();
        if (renderer != null && material != null) renderer.sharedMaterial = material;
    }

    private static void ConfigureLightAndSky(Camera camera)
    {
        RenderSettings.fog = true;
        RenderSettings.fogMode = FogMode.Linear;
        RenderSettings.fogColor = new Color(0.67f, 0.83f, 0.9f);
        RenderSettings.fogStartDistance = 75f;
        RenderSettings.fogEndDistance = 190f;
        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Skybox;
        RenderSettings.ambientIntensity = 0.9f;

        Shader skyShader = Shader.Find("Skybox/Procedural");
        if (skyShader != null)
        {
            const string skyPath = MaterialsFolder + "/ParcelPanic_SoftDaySky.mat";
            Material sky = AssetDatabase.LoadAssetAtPath<Material>(skyPath);
            if (sky == null)
            {
                sky = new Material(skyShader) { name = "ParcelPanic_SoftDaySky" };
                AssetDatabase.CreateAsset(sky, skyPath);
            }
            if (sky.HasProperty("_SkyTint")) sky.SetColor("_SkyTint", new Color(0.66f, 0.82f, 0.96f));
            if (sky.HasProperty("_GroundColor")) sky.SetColor("_GroundColor", new Color(0.47f, 0.61f, 0.68f));
            if (sky.HasProperty("_Exposure")) sky.SetFloat("_Exposure", 0.8f);
            if (sky.HasProperty("_AtmosphereThickness")) sky.SetFloat("_AtmosphereThickness", 0.75f);
            if (sky.HasProperty("_SunSize")) sky.SetFloat("_SunSize", 0.01f);
            EditorUtility.SetDirty(sky);
            RenderSettings.skybox = sky;
            RenderSettings.sun = null;
        }

        if (camera != null)
        {
            camera.clearFlags = CameraClearFlags.Skybox;
            camera.backgroundColor = new Color(0.6f, 0.8f, 0.95f);
            camera.farClipPlane = 1000f;
            camera.fieldOfView = 65f;
            camera.tag = "MainCamera";
        }

        Light sun = Object.FindFirstObjectByType<Light>();
        if (sun != null)
        {
            sun.type = LightType.Directional;
            sun.color = new Color(1f, 0.94f, 0.82f);
            sun.intensity = 1.15f;
            sun.transform.rotation = Quaternion.Euler(45f, -32f, 0f);
        }
    }

    private static void AddBackdrop(Transform parent, Material groundMaterial)
    {
        GameObject worldFloor = GameObject.CreatePrimitive(PrimitiveType.Cube);
        worldFloor.name = "ContinuousWorldFloor";
        worldFloor.transform.SetParent(parent, false);
        worldFloor.transform.position = new Vector3(0f, -0.07f, 0f);
        worldFloor.transform.localScale = new Vector3(600f, 0.1f, 600f);
        if (groundMaterial != null) SetMaterial(worldFloor, groundMaterial);
        Collider floorCollider = worldFloor.GetComponent<Collider>();
        if (floorCollider != null) floorCollider.enabled = true;

        Material hillMaterial = CreateMaterial("ParcelPanic_BackdropHills", new Color(0.48f, 0.73f, 0.66f));
        Transform hills = MakeGroup("DistantGreenHills", parent);
        Vector3[] positions =
        {
            new Vector3(0f, -1.5f, 68f), new Vector3(38f, -2f, 58f), new Vector3(68f, -1f, 18f),
            new Vector3(66f, -2f, -36f), new Vector3(18f, -1f, -68f), new Vector3(-36f, -2f, -65f),
            new Vector3(-70f, -1f, -26f), new Vector3(-65f, -2f, 38f)
        };
        for (int i = 0; i < positions.Length; i++)
        {
            GameObject hill = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            hill.name = "Hill_" + (i + 1);
            hill.transform.SetParent(hills, false);
            hill.transform.position = new Vector3(positions[i].x, -5f, positions[i].z);
            hill.transform.localScale = new Vector3(40f, 8f, 28f);
            SetMaterial(hill, hillMaterial);
            Collider collider = hill.GetComponent<Collider>();
            if (collider != null) collider.enabled = false;
        }
    }

    private static Material CreateMaterial(string name, Color color)
    {
        string path = MaterialsFolder + "/" + name + ".mat";
        Material material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (material == null)
        {
            Shader shader = Shader.Find("Standard");
            material = new Material(shader) { name = name, color = color };
            AssetDatabase.CreateAsset(material, path);
        }
        else
        {
            material.color = color;
            EditorUtility.SetDirty(material);
        }
        return material;
    }

    private static void EnsureEventSystem()
    {
        if (Object.FindFirstObjectByType<EventSystem>() != null) return;
        GameObject eventSystem = new GameObject("EventSystem", typeof(EventSystem), typeof(StandaloneInputModule));
    }
}
