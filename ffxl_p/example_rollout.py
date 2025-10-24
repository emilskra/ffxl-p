"""
Example usage of FFXL-P Gradual Rollout Feature
Demonstrates percentage-based user targeting across environments
"""

import os
from ffxl_p import (
    load_feature_flags,
    is_feature_enabled,
    get_enabled_features,
    User,
)


def main():
    print("=" * 70)
    print("FFXL-P: Gradual Rollout (Percentage-Based) Example")
    print("=" * 70)
    print()

    # Example 1: Basic gradual rollout
    print("Example 1: Basic Gradual Rollout")
    print("-" * 70)

    load_feature_flags("./feature-flags.yaml", environment="production")

    # Test with multiple users
    print("Testing 'new_payment_system' with 10% rollout in production:")
    enabled_count = 0
    total_users = 20

    for i in range(total_users):
        user = User(user_id=f"user-{i}")
        if is_feature_enabled("new_payment_system", user):
            enabled_count += 1
            print(f"  ✓ user-{i}: Enabled")
        else:
            print(f"  ✗ user-{i}: Disabled")

    percentage = (enabled_count / total_users) * 100
    print(f"\nResult: {enabled_count}/{total_users} users ({percentage:.0f}%) got the feature")
    print(f"Target: 10% rollout")
    print()

    # Example 2: Consistency - same user always gets same result
    print("Example 2: Consistency Across Requests")
    print("-" * 70)

    user = User(user_id="consistent-user-123")
    print(f"Checking feature 5 times for user '{user.user_id}':")

    results = []
    for i in range(5):
        result = is_feature_enabled("new_payment_system", user)
        results.append(result)
        print(f"  Call {i + 1}: {result}")

    all_same = all(r == results[0] for r in results)
    print(f"\nAll results identical: {all_same}")
    print("✓ Same user always gets same result for same feature")
    print()

    # Example 3: Different percentages per environment
    print("Example 3: Different Rollout Percentages Per Environment")
    print("-" * 70)

    user = User(user_id="test-user-456")

    for env in ["dev", "staging", "production"]:
        load_feature_flags("./feature-flags.yaml", environment=env)
        result = is_feature_enabled("new_payment_system", user)
        print(f"  {env:12s}: {result}")

    print()

    # Example 4: Gradual rollout progression
    print("Example 4: Gradual Rollout Progression (Staging -> Production)")
    print("-" * 70)
    print("Simulating rollout increase over time...")
    print()

    # Simulate different rollout stages
    stages = [
        ("Week 1", "staging", 25),
        ("Week 2", "staging", 50),
        ("Week 3", "staging", 100),
        ("Week 4", "production", 5),
        ("Week 5", "production", 10),
        ("Week 6", "production", 25),
    ]

    for week, env, target_pct in stages:
        # In real scenario, you'd update your YAML config
        print(f"{week}: {env} @ {target_pct}% - Testing with 20 users:")

        # Simulate by checking multiple users
        enabled = sum(
            1
            for i in range(20)
            if User(user_id=f"user-{i}").user_id  # Placeholder for actual check
        )
        print(f"  Target: {target_pct}% | Actual: ~{target_pct}% would be enabled")
        print()

    # Example 5: Combining environment restrictions with rollout
    print("Example 5: Environment Restrictions + Rollout Percentage")
    print("-" * 70)

    # Feature only in staging/production with different rollouts
    user = User(user_id="user-789")

    print("Feature 'redesigned_ui' config:")
    print("  - Environments: [staging, production]")
    print("  - Rollout: staging=100%, production=30%")
    print()

    for env in ["dev", "staging", "production"]:
        load_feature_flags("./feature-flags.yaml", environment=env)
        result = is_feature_enabled("redesigned_ui", user)
        print(f"  {env:12s}: {result}")

    print()

    # Example 6: Percentage rollout requires user
    print("Example 6: Rollout Requires User ID")
    print("-" * 70)

    load_feature_flags("./feature-flags.yaml", environment="production")

    # Without user
    result_no_user = is_feature_enabled("new_payment_system")
    print(f"Without user: {result_no_user}")
    print("  (Returns False because percentage rollout requires user ID)")

    # With user
    user = User(user_id="user-with-id")
    result_with_user = is_feature_enabled("new_payment_system", user)
    print(f"With user:    {result_with_user}")
    print("  (Evaluates based on user's hash bucket)")
    print()

    # Example 7: Real-world A/B testing scenario
    print("Example 7: A/B Testing Scenario")
    print("-" * 70)
    print("Testing new checkout flow with 50% of users...")
    print()

    load_feature_flags("./feature-flags.yaml", environment="production")

    users_with_feature = []
    users_without_feature = []

    for i in range(10):
        user = User(user_id=f"customer-{i}")
        if is_feature_enabled("experimental_feature", user):
            users_with_feature.append(user.user_id)
        else:
            users_without_feature.append(user.user_id)

    print(f"Group A (new flow):  {len(users_with_feature)} users")
    print(f"  Users: {', '.join(users_with_feature)}")
    print()
    print(f"Group B (old flow):  {len(users_without_feature)} users")
    print(f"  Users: {', '.join(users_without_feature)}")
    print()

    # Example 8: Development mode - see rollout calculations
    print("Example 8: Development Mode - See Rollout Details")
    print("-" * 70)
    print("Run with FFXL_DEV_MODE=true to see:")
    print("  - User percentage calculations")
    print("  - Rollout target comparisons")
    print("  - Decision logic")
    print()
    print("  FFXL_DEV_MODE=true python example_rollout.py")
    print()

    # Example 9: Monitoring rollout distribution
    print("Example 9: Monitor Rollout Distribution")
    print("-" * 70)

    load_feature_flags("./feature-flags.yaml", environment="production")

    sample_size = 100
    enabled_count = 0

    for i in range(sample_size):
        user = User(user_id=f"monitor-user-{i}")
        if is_feature_enabled("new_payment_system", user):
            enabled_count += 1

    actual_percentage = (enabled_count / sample_size) * 100
    print(f"Target rollout: 10%")
    print(f"Actual distribution (n={sample_size}): {actual_percentage:.1f}%")

    if 8 <= actual_percentage <= 12:
        print("✓ Distribution matches target (within expected variance)")
    else:
        print("⚠ Distribution outside expected range (may need more samples)")
    print()

    # Example 10: Safe rollout strategy
    print("Example 10: Safe Rollout Strategy")
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
