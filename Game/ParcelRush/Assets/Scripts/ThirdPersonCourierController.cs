using UnityEngine;

[RequireComponent(typeof(CharacterController))]
public class ThirdPersonCourierController : MonoBehaviour
{
    [Header("References")]
    public Transform cameraTransform;

    [Header("Movement")]
    [Tooltip("Metres per second. Keep close to Walk Animation Speed so the feet don't slide.")]
    public float walkSpeed = 1.35f;
    [Tooltip("Metres per second. Above ~2.2 m/s the walk cycle can't keep up: add a Run animation first.")]
    public float sprintSpeed = 2.2f;
    public float rotationSmoothTime = 0.1f;

    [Header("Animation")]
    public Animator animator;
    [Tooltip("Ground speed the Walk clip was made for (Blender walk cycle: 1.12 m/s).")]
    public float walkAnimationSpeed = 1.12f;

    [Header("Jumping")]
    public float jumpHeight = 1.5f;
    public float gravity = -20f;

    private CharacterController characterController;
    private float verticalVelocity;
    private float rotationVelocity;

    private void Awake()
    {
        characterController = GetComponent<CharacterController>();
    }

    private void Update()
    {
        bool grounded = characterController.isGrounded;
        if (grounded && verticalVelocity < 0f)
        {
            verticalVelocity = -2f;
        }

        float horizontal = Input.GetAxisRaw("Horizontal");
        float vertical = Input.GetAxisRaw("Vertical");
        Vector3 inputDirection = new Vector3(horizontal, 0f, vertical).normalized;
        float currentSpeed = 0f;

        if (inputDirection.sqrMagnitude > 0.01f)
        {
            float cameraYaw = cameraTransform != null ? cameraTransform.eulerAngles.y : 0f;
            float targetAngle = Mathf.Atan2(inputDirection.x, inputDirection.z) * Mathf.Rad2Deg + cameraYaw;
            float smoothAngle = Mathf.SmoothDampAngle(
                transform.eulerAngles.y,
                targetAngle,
                ref rotationVelocity,
                rotationSmoothTime
            );

            transform.rotation = Quaternion.Euler(0f, smoothAngle, 0f);
            float speed = Input.GetKey(KeyCode.LeftShift) ? sprintSpeed : walkSpeed;
            Vector3 moveDirection = Quaternion.Euler(0f, targetAngle, 0f) * Vector3.forward;
            characterController.Move(moveDirection.normalized * speed * Time.deltaTime);
            currentSpeed = speed;
        }

        if (animator != null)
        {
            // Speed switches Idle <-> Walk; MotionSpeed plays the walk faster/slower to match the ground speed
            animator.SetFloat("Speed", currentSpeed, 0.1f, Time.deltaTime);
            float playback = currentSpeed > 0.01f ? currentSpeed / walkAnimationSpeed : 1f;
            animator.SetFloat("MotionSpeed", Mathf.Clamp(playback, 0.5f, 2f));
        }

        if (grounded && Input.GetButtonDown("Jump"))
        {
            verticalVelocity = Mathf.Sqrt(jumpHeight * -2f * gravity);
        }

        verticalVelocity += gravity * Time.deltaTime;
        characterController.Move(Vector3.up * verticalVelocity * Time.deltaTime);
    }
}
