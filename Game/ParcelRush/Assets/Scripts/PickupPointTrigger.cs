using TMPro;
using UnityEngine;

public class PickupPointTrigger : MonoBehaviour
{
    public TMP_Text currentJobText;

    public static bool ParcelPickedUp { get; private set; }
    private bool pickedUp = false;

    private void Start()
    {
        ParcelPickedUp = false;
    }

    private void OnTriggerEnter(Collider other)
    {
        if (pickedUp || !other.CompareTag("Player"))
            return;

        pickedUp = true;
        ParcelPickedUp = true;

        if (currentJobText != null)
            currentJobText.text = "Deliver the parcel to the purple point";

        gameObject.SetActive(false);
    }
}