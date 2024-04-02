# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right


# def kthSmallest(root, k: int) -> int:
#     stack = []
#     while True:
#         while root:
#             stack.append(root)
#             root = root.left
#         root = stack.pop()
#         k -= 1
#         if k == 0:
#             return root.val
#         root = root.right       

# # Example usage:

# root2 = TreeNode(5)
# root2.left = TreeNode(3)
# root2.right = TreeNode(6)
# root2.left.left = TreeNode(2)
# root2.left.right = TreeNode(4)
# root2.left.left.left = TreeNode(1)

# k2 = 4
# print(kthSmallest(root2, k2))  # Output: 3            


# def merge_and_count(arr, left, mid, right, temp):
#     inv_count = 0
#     i = left
#     j = mid + 1
#     k = left
    
#     while i <= mid and j <= right:
#         if arr[i] <= arr[j]:
#             temp[k] = arr[i]
#             i += 1
#         else:
#             temp[k] = arr[j]
#             j += 1
#             inv_count += mid - i + 1
#         k += 1
    
#     while i <= mid:
#         temp[k] = arr[i]
#         i += 1
#         k += 1
    
#     while j <= right:
#         temp[k] = arr[j]
#         j += 1
#         k += 1
    
#     for i in range(left, right + 1):
#         arr[i] = temp[i]
    
#     return inv_count

# def merge_sort_and_count(arr, left, right, temp):
#     inv_count = 0
#     if left < right:
#         mid = (left + right) // 2
#         inv_count += merge_sort_and_count(arr, left, mid, temp)
#         inv_count += merge_sort_and_count(arr, mid + 1, right, temp)
#         inv_count += merge_and_count(arr, left, mid, right, temp)
#     return inv_count

# def getMinNumMoves(blocks):
#     n = len(blocks)
#     temp = [0] * n
#     return merge_sort_and_count(blocks, 0, n - 1, temp)

# # Example usage:
# blocks = [2,4,3,1,6]
# result = getMinNumMoves(blocks)
# print(result)  # Output should be 3

# def getMinNumMoves(blocks):
#     n = len(blocks)
#     moves = 0
#     for i in range(0, n):
#         if blocks[i] < blocks[i-1]:
#             moves += 1
#     return moves

# # Example usage:
# blocks = [3, 2, 1]
# print(getMinNumMoves(blocks))  # Output: 2

# def getMinNumMoves(blocks):
#     """
#     Calculates the minimum number of moves required to create good weight lifting equipment.

#     Args:
#         blocks (List[int]): An array of distinct weight values representing the blocks.

#     Returns:
#         int: The minimum number of moves required.
#     """

#     n = len(blocks)
#     inversions = 0

#     # Count inversions (pairs where a heavier block is before a lighter one)
#     for i in range(0, n):
#         for j in range(i + 1, n):
#             if blocks[i] > blocks[j]:
#                 inversions += 1

#     # Minimum moves required is equal to the number of inversions
#     return inversions

# # Example usage:
# blocks = [3, 2, 1]
# min_moves = getMinNumMoves(blocks)
# print(min_moves)  # Output: 3


# from collections import deque

# def findRequestsInQueue(wait):
#     n = len(wait)
#     queue = deque(range(1, n + 1))  # Initialize queue with request numbers
#     result = []

#     current_time = 0
#     for i in range(n):
#         while queue and current_time >= wait[queue[0] - 1]:  # Check if any request has expired
#             queue.popleft()  # Remove expired requests from the queue
#         result.append(len(queue))  # Append current queue length to result
#         if queue:  # Process the request if queue is not empty
#             queue.popleft()  # Serve the first request
#         current_time += 1  # Increment time

#     return result

# # Test the function
# print(findRequestsInQueue([3, 1, 2, 1]))  # Output: [4, 1, 0]
# print(findRequestsInQueue([4, 4, 4]))     # Output: [3, 2, 1, 0]

from collections import deque

# def count_requests(wait):
#     n = len(wait)
#     queue = []
#     requests_in_queue = []

#     for i in range(n):
#         expired_requests = 0
#         current_time = i + 1
#         while queue and current_time - queue[0] >= wait[i]:
#             queue.pop(0)
#             expired_requests += 1
#         requests_in_queue.append(len(queue))
#         queue.append(current_time)
    
#     return requests_in_queue

# # Example usage:
# wait = [3, 2, 1, 2]
# print(count_requests(wait))

# def getMinNumMoves(blocks):
#     n = len(blocks)
#     count = 1
    
#     # Iterate through the array and count the number of blocks not in their correct positions
#     for i in range(n):
#         if i + 1 != blocks[i]:
#             count += 1
    
#     # Minimum number of moves required is half of the count
#     return count // 2

# # Test cases
# blocks1 = [3, 2, 1]
# blocks2 = [4, 11, 9, 10, 12]

# print(getMinNumMoves(blocks1))  # Output: 3
# print(getMinNumMoves(blocks2))  # Output: 0