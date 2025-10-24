"""
Example usage of FFXL-P Gradual Rollout Feature
Demonstrates percentage-based user targeting across environments
"""

from ffxl_p import (
    is_feature_enabled,
    load_feature_flags,
)


def main():
    print("=" * 70)
    print("FFXL-P: Gradual Rollout (Percentage-Based) Example")
    print("=" * 70)
    print()

    # Example: Basic gradual rollout
    print("Example: Basic Gradual Rollout")
    print("-" * 70)

    load_feature_flags("./feature-flags.yaml", environment="production")

    # Test with multiple users
    print("Testing 'new_payment_system' with 10% rollout in production:")
    enabled_count = 0
    total_users = 20

    for i in range(total_users):
        user = f"user-{i}"
        if is_feature_enabled("new_payment_system", user):
            enabled_count += 1
            print(f"  ✓ user-{i}: Enabled")
        else:
            print(f"  ✗ user-{i}: Disabled")

    percentage = (enabled_count / total_users) * 100
    print(f"\nResult: {enabled_count}/{total_users} users ({percentage:.0f}%) got the feature")
    print("Target: 10% rollout")
    print()

    # Example: Consistency - same user always gets same result
    print("Example: Consistency Across Requests")
    print("-" * 70)

    user = "consistent-user-123"
    print(f"Checking feature 5 times for user '{user}':")

    results = []
    for i in range(5):
        result = is_feature_enabled("new_payment_system", user)
        results.append(result)
        print(f"  Call {i + 1}: {result}")

    all_same = all(r == results[0] for r in results)
    print(f"\nAll results identical: {all_same}")
    print("✓ Same user always gets same result for same feature")
    print()

    # Example: Different percentages per environment
    print("Example: Different Rollout Percentages Per Environment")
    print("-" * 70)

    user = "test-user-456"

    for env in ["dev", "staging", "production"]:
        load_feature_flags("./feature-flags.yaml", environment=env)
        result = is_feature_enabled("new_payment_system", user)
        print(f"  {env:12s}: {result}")

    print()

    # Example: Combining environment restrictions with rollout
    print("Example: Environment Restrictions + Rollout Percentage")
    print("-" * 70)

    # Feature only in staging/production with different rollouts
    user = "user-789"

    print("Feature 'redesigned_ui' config:")
    print("  - Environments: [staging, production]")
    print("  - Rollout: staging=100%, production=30%")
    print()

    for env in ["dev", "staging", "production"]:
        load_feature_flags("./feature-flags.yaml", environment=env)
        result = is_feature_enabled("redesigned_ui", user)
        print(f"  {env:12s}: {result}")

    print()

    # Example: Percentage rollout requires user
    print("Example: Rollout Requires User ID")
    print("-" * 70)

    load_feature_flags("./feature-flags.yaml", environment="production")

    # Without user
    result_no_user = is_feature_enabled("new_payment_system")
    print(f"Without user: {result_no_user}")
    print("  (Returns False because percentage rollout requires user ID)")

    # With user
    user = "user-with-id"
    result_with_user = is_feature_enabled("new_payment_system", user)
    print(f"With user:    {result_with_user}")
    print("  (Evaluates based on user's hash bucket)")
    print()

    # Example: Real-world A/B testing scenario
    print("Example: A/B Testing Scenario")
    print("-" * 70)
    print("Testing new checkout flow with 50% of users...")
    print()

    load_feature_flags("./feature-flags.yaml", environment="production")

    users_with_feature = []
    users_without_feature = []

    for i in range(10):
        user = f"customer-{i}"
        if is_feature_enabled("experimental_feature", user):
            users_with_feature.append(user)
        else:
            users_without_feature.append(user)

    print(f"Group A (new flow):  {len(users_with_feature)} users")
    print(f"  Users: {', '.join(users_with_feature)}")
    print()
    print(f"Group B (old flow):  {len(users_without_feature)} users")
    print(f"  Users: {', '.join(users_without_feature)}")
    print()

    # Example: Development mode - see rollout calculations
    print("Example: Development Mode - See Rollout Details")
    print("-" * 70)
    print("Run with FFXL_DEV_MODE=true to see:")
    print("  - User percentage calculations")
    print("  - Rollout target comparisons")
    print("  - Decision logic")
    print()
    print("  FFXL_DEV_MODE=true python example_rollout.py")
    print()

    # Example: Monitoring rollout distribution
    print("Example: Monitor Rollout Distribution")
    print("-" * 70)

    load_feature_flags("./feature-flags.yaml", environment="production")

    sample_size = 100
    enabled_count = 0

    for i in range(sample_size):
        user = f"monitor-user-{i}"
        if is_feature_enabled("new_payment_system", user):
            enabled_count += 1

    actual_percentage = (enabled_count / sample_size) * 100
    print("Target rollout: 10%")
    print(f"Actual distribution (n={sample_size}): {actual_percentage:.1f}%")

    if 8 <= actual_percentage <= 12:
        print("✓ Distribution matches target (within expected variance)")
    else:
        print("⚠ Distribution outside expected range (may need more samples)")
    print()

    # Example: Safe rollout strategy
    print("Example: Safe Rollout Strategy")
    print("-" * 70)
    print("Recommended rollout progression:")
    print()
    print("1. Dev:        100% - Full testing by team")
    print("2. Staging:    100% - QA and integration testing")
    print("3. Production:   5% - Initial real user exposure")
    print("4. Production:  10% - Monitor metrics")
    print("5. Production:  25% - Expand if stable")
    print("6. Production:  50% - Half of users")
    print("7. Production: 100% - Full rollout")
    print()
    print("Monitor key metrics at each stage:")
    print("  - Error rates")
    print("  - Performance metrics")
    print("  - User feedback")
    print("  - Business KPIs")
    print()


if __name__ == "__main__":
    main()
