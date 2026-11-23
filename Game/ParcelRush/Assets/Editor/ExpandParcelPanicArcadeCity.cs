using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

/// <summary>
/// Expands the current blockout into a connected, multi-district arcade city.
/// The generated area is grouped under Environment/ArcadeCityExtension for easy editing.
/// </summary>
public static class ExpandParcelPanicArcadeCity
{
    private const string MaterialsPath = "Assets/Materials/Parcel Panic Blockout";
    private static Material road, laneMark, roof, window, door, green, foliage, water, tyre;
    private static Material taxiYellow;
    private static Material[] buildingMaterials;

    [MenuItem("Tools/Parcel Panic/Expand to Arcade City")]
    private static void Build()
    {
        Transform environment = GameObject.Find("Environment")?.transform;
        GameObject ground = GameObject.Find("Ground");
        if (environment == null || ground == null)
        {
            EditorUtility.DisplayDialog("Open the combined town scene", "Open ParcelPanic_CompleteTown from Assets/Scenes, then run this command.", "OK");
            return;
        }

        EnsureMaterials();
        Transform previous = environment.Find("ArcadeCityExtension");
        if (previous != null) Object.DestroyImmediate(previous.gameObject);

        Transform root = Group("ArcadeCityExtension", environment);
        Transform roads = Group("ConnectedDistrictRoads", root);
        Transform buildings = Group("DistrictBuildings", root);
        Transform landmarks = Group("DistrictLandmarks", root);
        Transform cars = Group("ParkedVehicles", root);

        // Existing downtown loop and its four new links join this outer loop at every side.
        Vector2[] outer =
        {
            new Vector2(-66f, -46f), new Vector2(-46f, -66f), new Vector2(46f, -66f), new Vector2(66f, -46f),
            new Vector2(66f, 46f), new Vector2(46f, 66f), new Vector2(-46f, 66f), new Vector2(-66f, 46f)
        };
        for (int i = 0; i < outer.Length; i++)
            RoadBetween("OuterArcadeLoop_" + (i + 1), roads, outer[i], outer[(i + 1) % outer.Length], 7f, true);

        // Four broad boulevards meet the old loop and the new outer loop.
        RoadPolyline("NorthBoulevard", roads, new[] { new Vector2(0, 15), new Vector2(0, 34), new Vector2(-8, 43), new Vector2(-8, 54), new Vector2(0, 66) }, 7f);
        RoadPolyline("SouthBoulevard", roads, new[] { new Vector2(0, -15), new Vector2(0, -34), new Vector2(10, -43), new Vector2(10, -54), new Vector2(0, -66) }, 7f);
        RoadPolyline("WestBoulevard", roads, new[] { new Vector2(-18, 0), new Vector2(-34, 0), new Vector2(-44, 8), new Vector2(-54, 8), new Vector2(-66, 0) }, 7f);
        RoadPolyline("EastBoulevard", roads, new[] { new Vector2(18, 0), new Vector2(34, 0), new Vector2(44, -8), new Vector2(54, -8), new Vector2(66, 0) }, 7f);

        // Extra streets form connected choices through the four neighbourhoods.
        RoadPolyline("NorthNeighbourhoodStreet", roads, new[] { new Vector2(-59, 39), new Vector2(-34, 39), new Vector2(-17, 49), new Vector2(18, 49), new Vector2(37, 39), new Vector2(59, 39) }, 5f);
        RoadPolyline("SouthNeighbourhoodStreet", roads, new[] { new Vector2(-59, -39), new Vector2(-34, -39), new Vector2(-17, -49), new Vector2(18, -49), new Vector2(37, -39), new Vector2(59, -39) }, 5f);
        RoadPolyline("WestNeighbourhoodStreet", roads, new[] { new Vector2(-48, -43), new Vector2(-48, -16), new Vector2(-55, 0), new Vector2(-48, 16), new Vector2(-48, 43) }, 5f);
        RoadPolyline("EastNeighbourhoodStreet", roads, new[] { new Vector2(48, -43), new Vector2(48, -16), new Vector2(55, 0), new Vector2(48, 16), new Vector2(48, 43) }, 5f);

        // Apartment blocks in the north, a shop district east, homes west, depot south.
        AddRow(buildings, "NorthResidential", new[] { -56f, -27f, 20f, 55f }, 56f, new Vector3(6f, 7f, 6f), 0);
        AddRow(buildings, "NorthResidential", new[] { -56f, -27f, 20f, 55f }, 28f, new Vector3(5f, 5f, 5f), 0);
        AddRow(buildings, "WestHomes", new[] { -59f, -29f }, 27f, new Vector3(6f, 4f, 6f), 1);
        AddRow(buildings, "WestHomes", new[] { -59f, -29f }, -27f, new Vector3(5f, 5f, 5f), 1);
        AddRow(buildings, "EastMarket", new[] { 29f, 59f }, 27f, new Vector3(7f, 4f, 6f), 2);
        AddRow(buildings, "EastMarket", new[] { 29f, 59f }, -27f, new Vector3(5f, 6f, 5f), 2);
        AddRow(buildings, "SouthDepot", new[] { -55f, -27f, 20f, 55f }, -57f, new Vector3(8f, 5f, 7f), 3);
        AddRow(buildings, "SouthDepot", new[] { -55f, -27f, 20f, 55f }, -28f, new Vector3(6f, 4f, 6f), 3);

        BuildPark(landmarks, new Vector3(25f, 0f, 21f));
        BuildDepotLandmark(landmarks, new Vector3(38f, 0f, -56f));

        // Static non-colliding cars suggest traffic and give scale without blocking the courier.
        CreateCar(cars, "BlueCar", new Vector3(-8f, 0f, 32f), 0f, buildingMaterials[0]);
        CreateCar(cars, "TaxiYellow", new Vector3(32f, 0f, 0f), 90f, taxiYellow);
        CreateCar(cars, "DeliveryVan", new Vector3(-32f, 0f, -7f), 90f, buildingMaterials[3], true);
        CreateCar(cars, "CoralCar", new Vector3(10f, 0f, -32f), 0f, buildingMaterials[1]);
        CreateCar(cars, "ParkedCarNorth", new Vector3(25f, 0f, 57f), 0f, buildingMaterials[2]);
        CreateCar(cars, "ParkedCarWest", new Vector3(-59f, 0f, -6f), 90f, buildingMaterials[0]);

        ground.transform.localScale = new Vector3(160f, ground.transform.localScale.y, 150f);
        Collider groundCollider = ground.GetComponent<Collider>();
        if (groundCollider != null)
        {
            groundCollider.enabled = true;
            groundCollider.isTrigger = false;
        }

        Transform hills = GameObject.Find("DistantGreenHills")?.transform;
        if (hills != null)
        {
            Vector3[] hillPositions =
            {
                new Vector3(0f, -8f, 142f), new Vector3(95f, -8f, 105f), new Vector3(145f, -8f, 10f), new Vector3(105f, -8f, -105f),
                new Vector3(0f, -8f, -145f), new Vector3(-100f, -8f, -105f), new Vector3(-145f, -8f, 0f), new Vector3(-105f, -8f, 100f)
            };
            for (int i = 0; i < Mathf.Min(hills.childCount, hillPositions.Length); i++)
            {
                hills.GetChild(i).position = hillPositions[i];
                hills.GetChild(i).localScale = new Vector3(75f, 20f, 52f);
            }
        }

        Scene scene = SceneManager.GetActiveScene();
        if (scene.IsValid())
        {
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);
        }
        Selection.activeGameObject = root.gameObject;
        Debug.Log("Expanded Parcel Panic into a connected arcade city with four districts, curved streets, a park, a depot landmark, and parked vehicles.");
    }

    private static void AddRow(Transform root, string districtName, float[] xPositions, float z, Vector3 size, int palette)
    {
        Transform district = root.Find(districtName);
        if (district == null) district = Group(districtName, root);
        for (int i = 0; i < xPositions.Length; i++)
        {
            float width = size.x + ((i % 2 == 0) ? 0f : 1.5f);
            float height = size.y + ((i % 3 == 0) ? 1.5f : 0f);
            Vector3 buildingSize = new Vector3(width, height, size.z);
            CreateBuilding(district, districtName + "_Building_" + z.ToString("0") + "_" + i, new Vector3(xPositions[i], 0f, z), buildingSize, buildingMaterials[palette]);
        }
    }

    private static void CreateBuilding(Transform parent, string name, Vector3 groundPosition, Vector3 size, Material paint)
    {
        Transform group = Group(name, parent);
        Vector3 center = groundPosition + Vector3.up * size.y * 0.5f;
        Cube("Facade", group, center, size, paint, true);
        Cube("Roof", group, center + Vector3.up * (size.y * 0.5f + 0.12f), new Vector3(size.x + 0.2f, 0.24f, size.z + 0.2f), roof, false);
        float front = groundPosition.z - size.z * 0.5f - 0.04f;
        float windowY = groundPosition.y + size.y * 0.62f;
        Cube("WindowA", group, new Vector3(groundPosition.x - size.x * 0.24f, windowY, front), new Vector3(0.9f, 0.75f, 0.08f), window, false);
        Cube("WindowB", group, new Vector3(groundPosition.x + size.x * 0.24f, windowY, front), new Vector3(0.9f, 0.75f, 0.08f), window, false);
        Cube("Entrance", group, new Vector3(groundPosition.x, 0.95f, front - 0.02f), new Vector3(0.85f, 1.9f, 0.12f), door, false);
        Cube("Awning", group, new Vector3(groundPosition.x, 2.15f, front - 0.12f), new Vector3(size.x * 0.62f, 0.3f, 0.4f), (name.GetHashCode() & 1) == 0 ? roof : buildingMaterials[2], false);
    }

    private static void BuildPark(Transform parent, Vector3 center)
    {
        Transform park = Group("PocketPark", parent);
        Cube("ParkLawn", park, center + Vector3.up * 0.04f, new Vector3(14f, 0.08f, 12f), green, false);
        Vector2[] points = { new Vector2(-4.5f,-3.5f), new Vector2(4.5f,-3.5f), new Vector2(-4.5f,3.5f), new Vector2(4.5f,3.5f) };
        for (int i = 0; i < points.Length; i++)
        {
            Vector3 p = center + new Vector3(points[i].x, 0f, points[i].y);
            Cylinder("TreeTrunk_" + i, park, p + Vector3.up * 0.8f, new Vector3(0.35f, 0.8f, 0.35f), door, false);
            Sphere("TreeTop_" + i, park, p + Vector3.up * 2.05f, new Vector3(2.1f, 2.2f, 2.1f), foliage, false);
        }
        Cube("BenchSeat", park, center + new Vector3(0f, 0.55f, -5.5f), new Vector3(2.2f, 0.2f, 0.55f), door, false);
        Cylinder("Fountain", park, center + new Vector3(0f, 0.2f, 0f), new Vector3(1.5f, 0.2f, 1.5f), water, false);
    }

    private static void BuildDepotLandmark(Transform parent, Vector3 position)
    {
        Transform landmark = Group("ParcelDepot", parent);
        CreateBuilding(landmark, "LargeDepot", position, new Vector3(13f, 7f, 11f), buildingMaterials[3]);
        Cube("LoadingBay_A", landmark, position + new Vector3(-3.6f, 1.5f, -5.56f), new Vector3(2.2f, 2.8f, 0.12f), door, false);
        Cube("LoadingBay_B", landmark, position + new Vector3(3.6f, 1.5f, -5.56f), new Vector3(2.2f, 2.8f, 0.12f), door, false);
    }

    private static void CreateCar(Transform parent, string name, Vector3 position, float yaw, Material paint, bool van = false)
    {
        Transform car = Group(name, parent);
        car.position = position;
        car.rotation = Quaternion.Euler(0f, yaw, 0f);
        float length = van ? 3.7f : 2.8f;
        CubeLocal("Body", car, new Vector3(0f, 0.45f, 0f), new Vector3(length, 0.64f, 1.5f), paint);
        CubeLocal("Cabin", car, new Vector3(van ? -0.15f : 0f, 0.9f, 0f), new Vector3(van ? 1.8f : 1.45f, 0.5f, 1.15f), paint);
        if (name == "TaxiYellow")
            CubeLocal("TaxiRoofSign", car, new Vector3(0f, 1.22f, 0f), new Vector3(0.7f, 0.15f, 0.35f), laneMark);
        for (int x = -1; x <= 1; x += 2)
        for (int z = -1; z <= 1; z += 2)
            CubeLocal("Wheel", car, new Vector3(x * (length * 0.31f), 0.2f, z * 0.55f), new Vector3(0.48f, 0.36f, 0.22f), tyre);
    }

    private static void RoadPolyline(string name, Transform parent, Vector2[] points, float width)
    {
        for (int i = 0; i < points.Length - 1; i++)
            RoadBetween(name + "_" + (i + 1), parent, points[i], points[i + 1], width, true);
    }

    private static void RoadBetween(string name, Transform parent, Vector2 a, Vector2 b, float width, bool dashes)
    {
        Vector2 delta = b - a;
        float length = delta.magnitude;
        float yaw = Mathf.Atan2(-delta.y, delta.x) * Mathf.Rad2Deg;
        Vector2 midpoint = (a + b) * 0.5f;
        Cube(name, parent, new Vector3(midpoint.x, 0.06f, midpoint.y), new Vector3(length + 0.12f, 0.16f, width), road, true).transform.rotation = Quaternion.Euler(0f, yaw, 0f);
        if (!dashes || length < 7f) return;
        int count = Mathf.Max(1, Mathf.FloorToInt(length / 5f) - 1);
        for (int i = 0; i < count; i++)
        {
            float t = (i + 1f) / (count + 1f);
            Vector2 point = Vector2.Lerp(a, b, t);
            Cube("LaneDash", parent, new Vector3(point.x, 0.155f, point.y), new Vector3(1.3f, 0.025f, 0.14f), laneMark, false).transform.rotation = Quaternion.Euler(0f, yaw, 0f);
        }
    }

    private static Transform Group(string name, Transform parent)
    {
        GameObject group = new GameObject(name);
        group.transform.SetParent(parent, false);
        return group.transform;
    }

    private static GameObject Cube(string name, Transform parent, Vector3 position, Vector3 scale, Material material, bool collider)
    {
        GameObject item = GameObject.CreatePrimitive(PrimitiveType.Cube);
        item.name = name;
        item.transform.SetParent(parent, false);
        item.transform.position = position;
        item.transform.localScale = scale;
        Renderer renderer = item.GetComponent<Renderer>();
        if (renderer != null && material != null) renderer.sharedMaterial = material;
        Collider itemCollider = item.GetComponent<Collider>();
        if (itemCollider != null) itemCollider.enabled = collider;
        return item;
    }

    private static GameObject Cylinder(string name, Transform parent, Vector3 position, Vector3 scale, Material material, bool collider)
    {
        GameObject item = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        item.name = name;
        item.transform.SetParent(parent, false);
        item.transform.position = position;
        item.transform.localScale = scale;
        Renderer renderer = item.GetComponent<Renderer>();
        if (renderer != null && material != null) renderer.sharedMaterial = material;
        Collider itemCollider = item.GetComponent<Collider>();
        if (itemCollider != null) itemCollider.enabled = collider;
        return item;
    }

    private static GameObject Sphere(string name, Transform parent, Vector3 position, Vector3 scale, Material material, bool collider)
    {
        GameObject item = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        item.name = name;
        item.transform.SetParent(parent, false);
        item.transform.position = position;
        item.transform.localScale = scale;
        Renderer renderer = item.GetComponent<Renderer>();
        if (renderer != null && material != null) renderer.sharedMaterial = material;
        Collider itemCollider = item.GetComponent<Collider>();
        if (itemCollider != null) itemCollider.enabled = collider;
        return item;
    }

    private static void CubeLocal(string name, Transform parent, Vector3 localPosition, Vector3 scale, Material material)
    {
        GameObject item = GameObject.CreatePrimitive(PrimitiveType.Cube);
        item.name = name;
        item.transform.SetParent(parent, false);
        item.transform.localPosition = localPosition;
        item.transform.localScale = scale;
        Collider itemCollider = item.GetComponent<Collider>();
        if (itemCollider != null) itemCollider.enabled = false;
        Renderer renderer = item.GetComponent<Renderer>();
        if (renderer != null && material != null) renderer.sharedMaterial = material;
    }

    private static void EnsureMaterials()
    {
        if (!AssetDatabase.IsValidFolder("Assets/Materials")) AssetDatabase.CreateFolder("Assets", "Materials");
        if (!AssetDatabase.IsValidFolder(MaterialsPath)) AssetDatabase.CreateFolder("Assets/Materials", "Parcel Panic Blockout");
        road = MaterialAsset("Arcade_Road", new Color(0.25f, 0.29f, 0.36f));
        laneMark = MaterialAsset("Arcade_LaneMark", new Color(0.94f, 0.95f, 0.94f));
        roof = MaterialAsset("Arcade_Roof", new Color(0.25f, 0.58f, 0.82f));
        window = MaterialAsset("Arcade_Window", new Color(0.28f, 0.84f, 0.94f));
        door = MaterialAsset("Arcade_Door", new Color(0.35f, 0.2f, 0.16f));
        green = MaterialAsset("Arcade_ParkGrass", new Color(0.42f, 0.75f, 0.47f));
        foliage = MaterialAsset("Arcade_TreeCanopy", new Color(0.16f, 0.47f, 0.27f));
        water = MaterialAsset("Arcade_Fountain", new Color(0.2f, 0.68f, 0.88f));
        tyre = MaterialAsset("Arcade_Tyre", new Color(0.12f, 0.14f, 0.18f));
        taxiYellow = MaterialAsset("Arcade_TaxiYellow", new Color(0.98f, 0.72f, 0.06f));
        buildingMaterials = new[]
        {
            MaterialAsset("Arcade_BuildingTeal", new Color(0.18f, 0.61f, 0.67f)),
            MaterialAsset("Arcade_BuildingSand", new Color(0.78f, 0.59f, 0.36f)),
            MaterialAsset("Arcade_BuildingCoral", new Color(0.79f, 0.36f, 0.29f)),
            MaterialAsset("Arcade_BuildingBlue", new Color(0.24f, 0.43f, 0.72f))
        };
    }

    private static Material MaterialAsset(string name, Color color)
    {
        string path = MaterialsPath + "/" + name + ".mat";
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
}
