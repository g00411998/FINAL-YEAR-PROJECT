using TMPro;
using UnityEngine;

public class PickupPointTrigger : MonoBehaviour
{
    public TMP_Text currentJobText;
    public GameObject parcelVisual;

    public static bool ParcelPickedUp { get; private set; }
    private bool pickedUp = false;

    private void Start()
    {
        ParcelPickedUp = false;

        if (parcelVisual != null)
            parcelVisual.SetActive(false);
    }

    private void OnTriggerEnter(Collider other)
    {
        if (pickedUp || !other.CompareTag("Player"))
            return;

        pickedUp = true;
        ParcelPickedUp = true;

        if (parcelVisual != null)
            parcelVisual.SetActive(true);

        if (currentJobText != null)
            currentJobText.text = "CURRENT JOB\nDeliver the parcel to the purple point";

        gameObject.SetActive(false);
    }
}
