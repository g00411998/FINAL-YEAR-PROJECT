using System.Collections;
using TMPro;
using UnityEngine;

public class DeliveryPointTrigger : MonoBehaviour
{
    public TMP_Text currentJobText;
    public TMP_Text scoreText;
    public TMP_Text timerText;
    public TMP_Text deliveryCompleteText;
    public CanvasGroup deliveryCompleteGroup;

    private int score = 0;
    private float timeRemaining = 120f;
    private bool delivered = false;
    private bool timeUp = false;

    private void Start()
    {
        if (timerText != null)
            timerText.text = "TIME 02:00";

        if (scoreText != null)
            scoreText.text = "SCORE 000";

        if (currentJobText != null)
            currentJobText.text = "CURRENT JOB\nGo to the yellow pickup point";

        if (deliveryCompleteGroup != null)
        {
            deliveryCompleteGroup.alpha = 0f;
            deliveryCompleteGroup.gameObject.SetActive(false);
        }
    }

    private void Update()
    {
        if (timeRemaining <= 0f)
            return;

        timeRemaining -= Time.deltaTime;
        timeRemaining = Mathf.Max(timeRemaining, 0f);

        int seconds = Mathf.CeilToInt(timeRemaining);
        int minutes = seconds / 60;
        int remainingSeconds = seconds % 60;

        if (timerText != null)
            timerText.text = $"TIME {minutes:00}:{remainingSeconds:00}";

        if (timeRemaining <= 0f && !delivered && !timeUp)
        {
            timeUp = true;
            if (currentJobText != null)
                currentJobText.text = "CURRENT JOB\nTIME UP!";
        }
    }

    private void OnTriggerEnter(Collider other)
    {
        if (delivered || timeUp || !other.CompareTag("Player") || !PickupPointTrigger.ParcelPickedUp)
            return;

        delivered = true;
        score += 100;

        if (scoreText != null)
            scoreText.text = $"SCORE {score:000}";

        if (deliveryCompleteText != null)
            deliveryCompleteText.text = "DELIVERY COMPLETE!";

        if (deliveryCompleteGroup != null)
        {
            deliveryCompleteGroup.gameObject.SetActive(true);
            StartCoroutine(FadeInDeliveryComplete());
        }
    }

    private IEnumerator FadeInDeliveryComplete()
    {
        float elapsed = 0f;

        while (elapsed < 3f)
        {
            elapsed += Time.deltaTime;
            deliveryCompleteGroup.alpha = Mathf.Clamp01(elapsed / 3f);
            yield return null;
        }

        deliveryCompleteGroup.alpha = 1f;
    }
}
