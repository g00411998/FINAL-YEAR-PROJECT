using UnityEditor;
using UnityEngine;

/// <summary>
/// Creates a simple, editable town-loop blockout for the Parcel Panic practice scene.
/// It does not modify the existing Ground, Courier, PickupPoint, DeliveryPoint, UI,
/// camera, light, or EventSystem. Re-running it replaces only TownLoop_Blockout.
/// </summary>
public static class TownLoopBlockoutBuilder
{
    private const string RootName = "TownLoop_Blockout";
    private const string MaterialFolder = "Assets/Materials/Parcel Panic Blockout";

    private static Material blue;
    private static Material roofBlue;
    private static Material windowCyan;
    private static Material doorBrown;
    private static Material roadGrey;
    private static Material dashWhite;
    private static Material plazaGreen;
    private static Material treeGreen;
    private static Material fountainBlue;

    [MenuItem("Tools/Parcel Panic/Build Town Loop Blockout")]
    private static void BuildTownLoop()
    {
        GameObject existing = GameObject.Find(RootName);
        if (existing != null && !EditorUtility.DisplayDialog(
                "Rebuild Town Loop Blockout?",
                "This replaces only the generated TownLoop_Blockout group. Your existing scene objects will be kept.",
                "Rebuild", "Cancel"))
            return;

        EnsureMaterialFolder();
        LoadOrCreateMaterials();

        if (existing != null)
            Undo.DestroyObjectImmediate(existing);

        GameObject root = new GameObject(RootName);
        Undo.RegisterCreatedObjectUndo(root, "Build Town Loop Blockout");

        Transform environment = NewGroup("Environment", root.transform);
        Transform roads = NewGroup("Roads", environment);
        Transform plaza = NewGroup("CentralPlaza", environment);
        Transform buildings = NewGroup("Buildings", environment);

        BuildRoadLoop(roads);
        BuildPlaza(plaza);
        BuildBuildings(buildings);

        Selection.activeGameObject = root;
        EditorSceneManagerMarkDirty();
        Debug.Log("Town Loop Blockout created. Existing gameplay and UI objects were left untouched.");
    }

    private static void BuildRoadLoop(Transform parent)
    {
        // Fits approximately inside a 30 x 30 ground centred at (0, 0, 0).
        MakeCube("Road_Top", parent, new Vector3(0f, 0.055f, 8f), new Vector3(18f, 0.1f, 3.4f), roadGrey, false);
        MakeCube("Road_Bottom", parent, new Vector3(0f, 0.055f, -8f), new Vector3(18f, 0.1f, 3.4f), roadGrey, false);
        MakeCube("Road_Left", parent, new Vector3(-8f, 0.055f, 0f), new Vector3(3.4f, 0.1f, 18f), roadGrey, false);
        MakeCube("Road_Right", parent, new Vector3(8f, 0.055f, 0f), new Vector3(3.4f, 0.1f, 18f), roadGrey, false);

        Transform dashes = NewGroup("RoadDashes", parent);
        float[] marks = { -5f, -2f, 1f, 4f };
        foreach (float x in marks)
        {
            MakeCube("Dash_Top", dashes, new Vector3(x, 0.112f, 8f), new Vector3(0.9f, 0.025f, 0.12f), dashWhite, false);
            MakeCube("Dash_Bottom", dashes, new Vector3(x, 0.112f, -8f), new Vector3(0.9f, 0.025f, 0.12f), dashWhite, false);
        }
        foreach (float z in marks)
        {
            MakeCube("Dash_Left", dashes, new Vector3(-8f, 0.112f, z), new Vector3(0.12f, 0.025f, 0.9f), dashWhite, false);
            MakeCube("Dash_Right", dashes, new Vector3(8f, 0.112f, z), new Vector3(0.12f, 0.025f, 0.9f), dashWhite, false);
        }
    }

    private static void BuildPlaza(Transform parent)
    {
        MakeCube("PlazaGround", parent, new Vector3(0f, 0.06f, 0f), new Vector3(7.8f, 0.12f, 7.8f), plazaGreen, false);
        MakeCylinder("Fountain", parent, new Vector3(0f, 0.28f, 0f), new Vector3(1.2f, 0.22f, 1.2f), fountainBlue, false);

        Transform trees = NewGroup("Trees", parent);
        Vector3[] positions =
        {
            new Vector3(-2.6f, 0f, -2.6f), new Vector3(2.6f, 0f, -2.6f),
            new Vector3(-2.6f, 0f, 2.6f), new Vector3(2.6f, 0f, 2.6f)
        };
        for (int i = 0; i < positions.Length; i++)
        {
            Transform tree = NewGroup("Tree_" + (i + 1), trees);
            Vector3 p = positions[i];
            MakeCylinder("Trunk", tree, p + new Vector3(0f, 0.55f, 0f), new Vector3(0.28f, 0.55f, 0.28f), doorBrown, false);
            MakeSphere("Canopy", tree, p + new Vector3(0f, 1.45f, 0f), new Vector3(1.15f, 1.15f, 1.15f), treeGreen, false);
        }
    }

    private static void BuildBuildings(Transform parent)
    {
        Transform market = NewGroup("MarketDistrict", parent);
        Transform homes = NewGroup("ResidentialDistrict", parent);
        Transform services = NewGroup("PostOfficeAndCafe", parent);
        Transform depot = NewGroup("DepotDistrict", parent);

        MakeBuilding("CornerShop", market, new Vector3(-11f, 1.5f, 11.8f), new Vector3(4f, 3f, 3.5f));
        MakeBuilding("MarketHall", market, new Vector3(-4.5f, 1.8f, 11.8f), new Vector3(4.5f, 3.6f, 3.5f));
        MakeBuilding("Apartment_A", homes, new Vector3(4.5f, 1.8f, 11.8f), new Vector3(4f, 3.6f, 3.5f));
        MakeBuilding("Apartment_B", homes, new Vector3(11f, 1.5f, 11.8f), new Vector3(4f, 3f, 3.5f));
        MakeBuilding("Cafe", services, new Vector3(-11f, 1.5f, -11.8f), new Vector3(4f, 3f, 3.5f));
        MakeBuilding("PostOffice", services, new Vector3(-4.5f, 1.5f, -11.8f), new Vector3(4f, 3f, 3.5f));
        MakeBuilding("Warehouse", depot, new Vector3(4.5f, 2f, -11.8f), new Vector3(5f, 4f, 4f));
        MakeBuilding("Garage", depot, new Vector3(11f, 1.5f, -11.8f), new Vector3(4f, 3f, 3.5f));
    }

    private static void MakeBuilding(string name, Transform parent, Vector3 position, Vector3 size)
    {
        Transform group = NewGroup(name, parent);
        MakeCube("BuildingBody", group, position, size, blue, true);

        float frontZ = position.z - size.z * 0.5f - 0.035f;
        float windowY = position.y + size.y * 0.12f;
        float windowWidth = Mathf.Min(0.75f, size.x * 0.22f);
        float windowHeight = Mathf.Min(0.65f, size.y * 0.24f);
        MakeCube("Window_Left", group, new Vector3(position.x - size.x * 0.22f, windowY, frontZ), new Vector3(windowWidth, windowHeight, 0.07f), windowCyan, false);
        MakeCube("Window_Right", group, new Vector3(position.x + size.x * 0.22f, windowY, frontZ), new Vector3(windowWidth, windowHeight, 0.07f), windowCyan, false);
        MakeCube("Door", group, new Vector3(position.x, 0.85f, frontZ - 0.01f), new Vector3(0.8f, 1.7f, 0.1f), doorBrown, false);

        // Thin lighter roof cap helps distinguish building tops in the Scene view.
        MakeCube("RoofTrim", group, new Vector3(position.x, position.y + size.y * 0.5f + 0.06f, position.z), new Vector3(size.x + 0.12f, 0.12f, size.z + 0.12f), roofBlue, false);
    }

    private static GameObject MakeCube(string name, Transform parent, Vector3 position, Vector3 scale, Material material, bool colliderEnabled)
    {
        GameObject obj = GameObject.CreatePrimitive(PrimitiveType.Cube);
        obj.name = name;
        obj.transform.SetParent(parent, false);
        obj.transform.position = position;
        obj.transform.localScale = scale;
        SetMaterial(obj, material);
        SetCollider(obj, colliderEnabled);
        Undo.RegisterCreatedObjectUndo(obj, "Create " + name);
        return obj;
    }

    private static GameObject MakeCylinder(string name, Transform parent, Vector3 position, Vector3 scale, Material material, bool colliderEnabled)
    {
        GameObject obj = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        obj.name = name;
        obj.transform.SetParent(parent, false);
        obj.transform.position = position;
        obj.transform.localScale = scale;
        SetMaterial(obj, material);
        SetCollider(obj, colliderEnabled);
        Undo.RegisterCreatedObjectUndo(obj, "Create " + name);
        return obj;
    }

    private static GameObject MakeSphere(string name, Transform parent, Vector3 position, Vector3 scale, Material material, bool colliderEnabled)
    {
        GameObject obj = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        obj.name = name;
        obj.transform.SetParent(parent, false);
        obj.transform.position = position;
        obj.transform.localScale = scale;
        SetMaterial(obj, material);
        SetCollider(obj, colliderEnabled);
        Undo.RegisterCreatedObjectUndo(obj, "Create " + name);
        return obj;
    }

    private static Transform NewGroup(string name, Transform parent)
    {
        GameObject group = new GameObject(name);
        group.transform.SetParent(parent, false);
        Undo.RegisterCreatedObjectUndo(group, "Create " + name);
        return group.transform;
    }

    private static void SetMaterial(GameObject obj, Material material)
    {
        Renderer renderer = obj.GetComponent<Renderer>();
        if (renderer != null)
            renderer.sharedMaterial = material;
    }

    private static void SetCollider(GameObject obj, bool enabled)
    {
        Collider collider = obj.GetComponent<Collider>();
        if (collider != null)
            collider.enabled = enabled;
    }

    private static void EnsureMaterialFolder()
    {
        if (!AssetDatabase.IsValidFolder("Assets/Materials"))
            AssetDatabase.CreateFolder("Assets", "Materials");
        if (!AssetDatabase.IsValidFolder(MaterialFolder))
            AssetDatabase.CreateFolder("Assets/Materials", "Parcel Panic Blockout");
    }

    private static void LoadOrCreateMaterials()
    {
        blue = GetMaterial("Blockout_Blue", new Color(0.17f, 0.42f, 0.78f));
        roofBlue = GetMaterial("Blockout_RoofBlue", new Color(0.35f, 0.72f, 0.93f));
        windowCyan = GetMaterial("Blockout_WindowCyan", new Color(0.45f, 0.9f, 0.95f));
        doorBrown = GetMaterial("Blockout_DoorBrown", new Color(0.42f, 0.23f, 0.14f));
        roadGrey = GetMaterial("Blockout_RoadGrey", new Color(0.34f, 0.39f, 0.46f));
        dashWhite = GetMaterial("Blockout_RoadWhite", new Color(0.94f, 0.96f, 0.98f));
        plazaGreen = GetMaterial("Blockout_PlazaGreen", new Color(0.72f, 0.9f, 0.78f));
        treeGreen = GetMaterial("Blockout_TreeGreen", new Color(0.18f, 0.58f, 0.31f));
        fountainBlue = GetMaterial("Blockout_FountainBlue", new Color(0.2f, 0.68f, 0.88f));
    }

    private static Material GetMaterial(string materialName, Color color)
    {
        string path = MaterialFolder + "/" + materialName + ".mat";
        Material material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (material == null)
        {
            Shader shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null) shader = Shader.Find("Standard");
            if (shader == null) shader = Shader.Find("Diffuse");
            material = new Material(shader) { name = materialName };
            AssetDatabase.CreateAsset(material, path);
        }

        if (material.HasProperty("_BaseColor")) material.SetColor("_BaseColor", color);
        if (material.HasProperty("_Color")) material.SetColor("_Color", color);
        EditorUtility.SetDirty(material);
        return material;
    }

    private static void EditorSceneManagerMarkDirty()
    {
        if (UnityEditor.SceneManagement.EditorSceneManager.GetActiveScene().IsValid())
            UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(UnityEditor.SceneManagement.EditorSceneManager.GetActiveScene());
    }
}
