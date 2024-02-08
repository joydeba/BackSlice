def permute(nums):
    def backtrack(start):
        if start == len(nums):
            result.append(nums.copy())
            return

        for i in range(start, len(nums)):
            # Swap elements to generate permutations
            nums[start], nums[i] = nums[i], nums[start]
            # Recursively generate permutations for the rest of the array
            backtrack(start + 1)
            # Backtrack: undo the swap for the next iteration
            nums[start], nums[i] = nums[i], nums[start]

    result = []
    backtrack(0)
    return result

# Example usage:
nums1 = [1, 2, 3]
print(permute(nums1))

nums2 = [0, 1]
print(permute(nums2))

nums3 = [1]
print(permute(nums3))