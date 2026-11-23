using UnityEditor;
using UnityEngine;
using UnityEngine.SceneManagement;

/// <summary>
/// Adds a larger, irregular connected town blockout to the active scene.
/// It resizes the active scene's object named Ground, then creates/replaces only
/// Expanded_Town_Loop. It does not move or delete the courier, UI, or job markers.
/// </summary>
public static class ExpandedTownLoopBuilder
{
    private const string RootName = "Expanded_Town_Loop";
    private const string PreviousGeneratedRootName = "TownLoop_Blockout";
    private const string MaterialFolder = "Assets/Materials/Parcel Panic Blockout";

    private static Material blue, roofBlue, window, brown, road, dash, park, leaves, water;

    [MenuItem("Tools/Parcel Panic/Build Expanded Connected Town Loop")]
    private static void Build()
    {
        GameObject ground = GameObject.Find("Ground");
        if (ground == null)
        {
            EditorUtility.DisplayDialog("Ground not found", "This builder needs an active scene object named Ground. Rename your main floor object to Ground, then run the menu again.", "OK");
            return;
        }

        GameObject previous = GameObject.Find(RootName);
        GameObject previousGeneratedRoot = GameObject.Find(PreviousGeneratedRootName);
        if (!EditorUtility.DisplayDialog(
                "Build expanded town layout?",
                "This enlarges Ground to 50 x 42 units and replaces the generated TownLoop_Blockout / Expanded_Town_Loop groups. Your gameplay and UI objects are kept. Save a copy of your scene first.",
                "Build", "Cancel"))
            return;

        EnsureMaterials();
        Undo.RecordObject(ground.transform, "Enlarge town ground");
        Vector3 oldScale = ground.transform.localScale;
        ground.transform.localScale = new Vector3(50f, oldScale.y, 42f);
        ground.SetActive(true);
        Collider floorCollider = ground.GetComponent<Collider>();
        if (floorCollider != null)
        {
            Undo.RecordObject(floorCollider, "Enable ground collider");
            floorCollider.enabled = true;
            floorCollider.isTrigger = false;
        }

        if (previous != null)
            Undo.DestroyObjectImmediate(previous);
        if (previousGeneratedRoot != null)
            Undo.DestroyObjectImmediate(previousGeneratedRoot);

        GameObject root = new GameObject(RootName);
        Undo.RegisterCreatedObjectUndo(root, "Build expanded town layout");
        Transform environment = Group("Environment", root.transform);
        Transform roads = Group("Roads", environment);
        Transform plaza = Group("CentralPlaza", environment);
        Transform districts = Group("Districts", environment);

        BuildLoopAndStreets(roads);
        BuildPlaza(plaza);
        BuildDistricts(districts);

        Selection.activeGameObject = root;
        Scene active = SceneManager.GetActiveScene();
        if (active.IsValid()) UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(active);
        Debug.Log("Expanded town loop built. Reposition your existing PickupPoint and DeliveryPoint on the new roads if needed.");
    }

    private static void BuildLoopAndStreets(Transform parent)
    {
        // Uneven octagonal ring: long north/south runs, angled corners, and two route choices.
        Vector2[] loop =
        {
            new Vector2(-18f, -9f), new Vector2(-12f, -15f), new Vector2(10f, -15f),
            new Vector2(18f, -8f), new Vector2(18f, 8f), new Vector2(10f, 15f),
            new Vector2(-12f, 15f), new Vector2(-18f, 9f)
        };
        Transform ring = Group("IrregularTownLoop", parent);
        for (int i = 0; i < loop.Length; i++)
            RoadBetween("LoopRoad_" + (i + 1), ring, loop[i], loop[(i + 1) % loop.Length], 4.2f, true);

        // A bent shortcut across the inside links the west and east sides of the loop.
        Transform shortcut = Group("BentInnerStreet", parent);
        Vector2[] inner =
        {
            new Vector2(-18f, 0f), new Vector2(-10f, 0f), new Vector2(-5f, 5f),
            new Vector2(5f, 5f), new Vector2(10f, 0f), new Vector2(18f, 0f)
        };
        for (int i = 0; i < inner.Length - 1; i++)
            RoadBetween("InnerRoad_" + (i + 1), shortcut, inner[i], inner[i + 1], 3.8f, true);

        // Small branch streets add destinations off the loop without making a maze.
        Transform branches = Group("DistrictBranches", parent);
        RoadBetween("MarketBranch", branches, new Vector2(-15f, 12f), new Vector2(-21f, 18f), 3.4f, false);
        RoadBetween("DepotBranch", branches, new Vector2(14f, -11f), new Vector2(21f, -18f), 3.4f, false);
    }

    private static void RoadBetween(string name, Transform parent, Vector2 a, Vector2 b, float width, bool addDashes)
    {
        Vector2 delta = b - a;
        float length = delta.magnitude + 0.15f;
        float yaw = Mathf.Atan2(-delta.y, delta.x) * Mathf.Rad2Deg;
        Vector2 middle = (a + b) * 0.5f;
        GameObject segment = Cube(name, parent, new Vector3(middle.x, 0.06f, middle.y), new Vector3(length, 0.12f, width), road, false);
        segment.transform.rotation = Quaternion.Euler(0f, yaw, 0f);

        if (!addDashes || length < 5f) return;
        Transform marks = Group(name + "_Dashes", parent);
        int count = Mathf.Max(1, Mathf.FloorToInt(length / 3.5f) - 1);
        Vector2 direction = delta.normalized;
        for (int i = 0; i < count; i++)
        {
            float t = (i + 1f) / (count + 1f);
            Vector2 point = Vector2.Lerp(a, b, t);
            GameObject mark = Cube("Dash", marks, new Vector3(point.x, 0.14f, point.y), new Vector3(0.9f, 0.025f, 0.12f), dash, false);
            mark.transform.rotation = Quaternion.Euler(0f, yaw, 0f);
        }
    }

    private static void BuildPlaza(Transform parent)
    {
        Cube("PlazaGround", parent, new Vector3(0f, 0.055f, -5.5f), new Vector3(8f, 0.11f, 6.2f), park, false);
        Cylinder("Fountain", parent, new Vector3(0f, 0.28f, -5.5f), new Vector3(1.25f, 0.22f, 1.25f), water, false);
        Transform trees = Group("PlazaTrees", parent);
        Vector2[] spots = { new Vector2(-2.7f,-7.3f), new Vector2(2.7f,-7.3f), new Vector2(-2.7f,-3.7f), new Vector2(2.7f,-3.7f) };
        for (int i = 0; i < spots.Length; i++)
        {
            Transform tree = Group("Tree_" + (i + 1), trees);
            Vector2 p = spots[i];
            Cylinder("Trunk", tree, new Vector3(p.x, 0.55f, p.y), new Vector3(0.28f, 0.55f, 0.28f), brown, false);
            Sphere("Canopy", tree, new Vector3(p.x, 1.4f, p.y), new Vector3(1.15f, 1.15f, 1.15f), leaves, false);
        }
    }

    private static void BuildDistricts(Transform parent)
    {
        Transform market = Group("MarketDistrict", parent);
        Transform homes = Group("ResidentialDistrict", parent);
        Transform civic = Group("CivicDistrict", parent);
        Transform depot = Group("WarehouseDistrict", parent);

        Building("MarketHall", market, new Vector3(-21.5f, 1.7f, 12.3f), new Vector3(4.5f, 3.4f, 4f));
        Building("CornerShop", market, new Vector3(-21.5f, 1.5f, 5.8f), new Vector3(4f, 3f, 3.5f));
        Building("Apartment_A", homes, new Vector3(-6.5f, 1.7f, 18.7f), new Vector3(4.4f, 3.4f, 3.4f));
        Building("Apartment_B", homes, new Vector3(0f, 1.5f, 18.7f), new Vector3(4f, 3f, 3.4f));
        Building("Apartment_C", homes, new Vector3(6.5f, 1.7f, 18.7f), new Vector3(4.4f, 3.4f, 3.4f));
        Building("Cafe", civic, new Vector3(-21.5f, 1.5f, -5.5f), new Vector3(4f, 3f, 3.5f));
        Building("PostOffice", civic, new Vector3(21.5f, 1.8f, 5.8f), new Vector3(4.2f, 3.6f, 3.5f));
        Building("Library", civic, new Vector3(21.5f, 1.5f, 0f), new Vector3(4f, 3f, 3.5f));
        Building("Warehouse", depot, new Vector3(21.5f, 2f, -12f), new Vector3(5f, 4f, 4.5f));
        Building("Garage", depot, new Vector3(15f, 1.5f, -18.5f), new Vector3(4f, 3f, 3.5f));
    }

    private static void Building(string name, Transform parent, Vector3 position, Vector3 size)
    {
        Transform group = Group(name, parent);
        Cube("BuildingBody", group, position, size, blue, true);
        float frontZ = position.z - size.z * 0.5f - 0.04f;
        float windowY = position.y + size.y * 0.12f;
        Cube("Window_Left", group, new Vector3(position.x - size.x * 0.22f, windowY, frontZ), new Vector3(0.75f, 0.6f, 0.07f), window, false);
        Cube("Window_Right", group, new Vector3(position.x + size.x * 0.22f, windowY, frontZ), new Vector3(0.75f, 0.6f, 0.07f), window, false);
        Cube("Door", group, new Vector3(position.x, 0.85f, frontZ - 0.02f), new Vector3(0.8f, 1.7f, 0.1f), brown, false);
        Cube("RoofTrim", group, new Vector3(position.x, position.y + size.y * 0.5f + 0.06f, position.z), new Vector3(size.x + 0.12f, 0.12f, size.z + 0.12f), roofBlue, false);
    }

    private static Transform Group(string name, Transform parent)
    {
        GameObject obj = new GameObject(name);
        obj.transform.SetParent(parent, false);
        Undo.RegisterCreatedObjectUndo(obj, "Create " + name);
        return obj.transform;
    }

    private static GameObject Cube(string name, Transform parent, Vector3 position, Vector3 scale, Material mat, bool colliderEnabled)
    {
        return Primitive(name, parent, PrimitiveType.Cube, position, scale, mat, colliderEnabled);
    }

    private static GameObject Cylinder(string name, Transform parent, Vector3 position, Vector3 scale, Material mat, bool colliderEnabled)
    {
        return Primitive(name, parent, PrimitiveType.Cylinder, position, scale, mat, colliderEnabled);
    }

    private static GameObject Sphere(string name, Transform parent, Vector3 position, Vector3 scale, Material mat, bool colliderEnabled)
    {
        return Primitive(name, parent, PrimitiveType.Sphere, position, scale, mat, colliderEnabled);
    }

    private static GameObject Primitive(string name, Transform parent, PrimitiveType type, Vector3 position, Vector3 scale, Material mat, bool colliderEnabled)
    {
        GameObject obj = GameObject.CreatePrimitive(type);
        obj.name = name;
        obj.transform.SetParent(parent, false);
        obj.transform.position = position;
        obj.transform.localScale = scale;
        Renderer renderer = obj.GetComponent<Renderer>();
        if (renderer != null) renderer.sharedMaterial = mat;
        Collider collider = obj.GetComponent<Collider>();
        if (collider != null) collider.enabled = colliderEnabled;
        Undo.RegisterCreatedObjectUndo(obj, "Create " + name);
        return obj;
    }

    private static void EnsureMaterials()
    {
        if (!AssetDatabase.IsValidFolder("Assets/Materials")) AssetDatabase.CreateFolder("Assets", "Materials");
        if (!AssetDatabase.IsValidFolder(MaterialFolder)) AssetDatabase.CreateFolder("Assets/Materials", "Parcel Panic Blockout");
        blue = Mat("Blockout_Blue", new Color(0.17f, 0.42f, 0.78f));
        roofBlue = Mat("Blockout_RoofBlue", new Color(0.35f, 0.72f, 0.93f));
        window = Mat("Blockout_WindowCyan", new Color(0.45f, 0.9f, 0.95f));
        brown = Mat("Blockout_DoorBrown", new Color(0.42f, 0.23f, 0.14f));
        road = Mat("Blockout_RoadGrey", new Color(0.34f, 0.39f, 0.46f));
        dash = Mat("Blockout_RoadWhite", new Color(0.94f, 0.96f, 0.98f));
        park = Mat("Blockout_PlazaGreen", new Color(0.72f, 0.9f, 0.78f));
        leaves = Mat("Blockout_TreeGreen", new Color(0.18f, 0.58f, 0.31f));
        water = Mat("Blockout_FountainBlue", new Color(0.2f, 0.68f, 0.88f));
    }

    private static Material Mat(string name, Color color)
    {
        string path = MaterialFolder + "/" + name + ".mat";
        Material mat = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (mat == null)
        {
            Shader shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null) shader = Shader.Find("Standard");
            if (shader == null) shader = Shader.Find("Diffuse");
            if (shader == null)
            {
                Debug.LogError("Could not find a supported shader to create the blockout materials.");
                return null;
            }
            mat = new Material(shader) { name = name };
            AssetDatabase.CreateAsset(mat, path);
        }
        if (mat.HasProperty("_BaseColor")) mat.SetColor("_BaseColor", color);
        if (mat.HasProperty("_Color")) mat.SetColor("_Color", color);
        EditorUtility.SetDirty(mat);
        return mat;
    }
}
