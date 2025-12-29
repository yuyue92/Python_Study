"""
Python 算法与数据结构完整实现指南
包含详细讲解和时间复杂度分析
"""

# ============================================================================
# 第一部分: 基础数据结构
# ============================================================================

# 1. 链表 (Linked List)
# ----------------------------------------------------------------------------
class Node:
    """链表节点"""
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    """
    单向链表实现
    特点: 动态大小，插入删除O(1)，查找O(n)
    """
    def __init__(self):
        self.head = None
    
    def append(self, data):
        """在末尾添加节点 - O(n)"""
        new_node = Node(data)
        if not self.head:
            self.head = new_node
            return
        current = self.head
        while current.next:
            current = current.next
        current.next = new_node
    
    def prepend(self, data):
        """在开头添加节点 - O(1)"""
        new_node = Node(data)
        new_node.next = self.head
        self.head = new_node
    
    def delete(self, data):
        """删除指定值的节点 - O(n)"""
        if not self.head:
            return
        if self.head.data == data:
            self.head = self.head.next
            return
        current = self.head
        while current.next:
            if current.next.data == data:
                current.next = current.next.next
                return
            current = current.next
    
    def display(self):
        """显示链表"""
        elements = []
        current = self.head
        while current:
            elements.append(str(current.data))
            current = current.next
        return " -> ".join(elements)


# 2. 栈 (Stack)
# ----------------------------------------------------------------------------
class Stack:
    """
    栈实现 - LIFO (后进先出)
    应用: 函数调用栈、括号匹配、深度优先搜索
    所有操作: O(1)
    """
    def __init__(self):
        self.items = []
    
    def push(self, item):
        """入栈"""
        self.items.append(item)
    
    def pop(self):
        """出栈"""
        if not self.is_empty():
            return self.items.pop()
        return None
    
    def peek(self):
        """查看栈顶元素"""
        if not self.is_empty():
            return self.items[-1]
        return None
    
    def is_empty(self):
        return len(self.items) == 0
    
    def size(self):
        return len(self.items)


# 3. 队列 (Queue)
# ----------------------------------------------------------------------------
from collections import deque

class Queue:
    """
    队列实现 - FIFO (先进先出)
    应用: 广度优先搜索、任务调度、缓冲区
    所有操作: O(1)
    """
    def __init__(self):
        self.items = deque()
    
    def enqueue(self, item):
        """入队"""
        self.items.append(item)
    
    def dequeue(self):
        """出队"""
        if not self.is_empty():
            return self.items.popleft()
        return None
    
    def front(self):
        """查看队首元素"""
        if not self.is_empty():
            return self.items[0]
        return None
    
    def is_empty(self):
        return len(self.items) == 0
    
    def size(self):
        return len(self.items)


# 4. 二叉树 (Binary Tree)
# ----------------------------------------------------------------------------
class TreeNode:
    """二叉树节点"""
    def __init__(self, data):
        self.data = data
        self.left = None
        self.right = None

class BinaryTree:
    """
    二叉树实现
    包含三种遍历方式
    """
    def __init__(self):
        self.root = None
    
    def inorder_traversal(self, node, result=None):
        """
        中序遍历: 左 -> 根 -> 右
        对于二叉搜索树，结果是有序的
        时间复杂度: O(n)
        """
        if result is None:
            result = []
        if node:
            self.inorder_traversal(node.left, result)
            result.append(node.data)
            self.inorder_traversal(node.right, result)
        return result
    
    def preorder_traversal(self, node, result=None):
        """
        前序遍历: 根 -> 左 -> 右
        用于复制树结构
        时间复杂度: O(n)
        """
        if result is None:
            result = []
        if node:
            result.append(node.data)
            self.preorder_traversal(node.left, result)
            self.preorder_traversal(node.right, result)
        return result
    
    def postorder_traversal(self, node, result=None):
        """
        后序遍历: 左 -> 右 -> 根
        用于删除树
        时间复杂度: O(n)
        """
        if result is None:
            result = []
        if node:
            self.postorder_traversal(node.left, result)
            self.postorder_traversal(node.right, result)
            result.append(node.data)
        return result
    
    def level_order_traversal(self, root):
        """
        层序遍历 (广度优先)
        使用队列实现
        时间复杂度: O(n)
        """
        if not root:
            return []
        result = []
        queue = deque([root])
        while queue:
            node = queue.popleft()
            result.append(node.data)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        return result


# 5. 二叉搜索树 (Binary Search Tree)
# ----------------------------------------------------------------------------
class BST:
    """
    二叉搜索树: 左子树 < 根 < 右子树
    查找、插入、删除平均: O(log n)
    最坏情况(退化成链表): O(n)
    """
    def __init__(self):
        self.root = None
    
    def insert(self, data):
        """插入节点"""
        if not self.root:
            self.root = TreeNode(data)
        else:
            self._insert_recursive(self.root, data)
    
    def _insert_recursive(self, node, data):
        if data < node.data:
            if node.left is None:
                node.left = TreeNode(data)
            else:
                self._insert_recursive(node.left, data)
        else:
            if node.right is None:
                node.right = TreeNode(data)
            else:
                self._insert_recursive(node.right, data)
    
    def search(self, data):
        """搜索节点"""
        return self._search_recursive(self.root, data)
    
    def _search_recursive(self, node, data):
        if node is None or node.data == data:
            return node
        if data < node.data:
            return self._search_recursive(node.left, data)
        return self._search_recursive(node.right, data)
    
    def find_min(self, node):
        """找到最小值节点"""
        current = node
        while current.left:
            current = current.left
        return current
    
    def delete(self, data):
        """删除节点"""
        self.root = self._delete_recursive(self.root, data)
    
    def _delete_recursive(self, node, data):
        if not node:
            return node
        
        if data < node.data:
            node.left = self._delete_recursive(node.left, data)
        elif data > node.data:
            node.right = self._delete_recursive(node.right, data)
        else:
            # 找到要删除的节点
            if not node.left:
                return node.right
            elif not node.right:
                return node.left
            # 有两个子节点：找右子树的最小值
            temp = self.find_min(node.right)
            node.data = temp.data
            node.right = self._delete_recursive(node.right, temp.data)
        
        return node


# 6. 堆 (Heap)
# ----------------------------------------------------------------------------
import heapq

class MinHeap:
    """
    最小堆实现
    父节点总是小于子节点
    插入、删除: O(log n)
    查找最小值: O(1)
    应用: 优先队列、堆排序、Top K问题
    """
    def __init__(self):
        self.heap = []
    
    def push(self, item):
        """插入元素"""
        heapq.heappush(self.heap, item)
    
    def pop(self):
        """弹出最小元素"""
        if self.heap:
            return heapq.heappop(self.heap)
        return None
    
    def peek(self):
        """查看最小元素"""
        return self.heap[0] if self.heap else None
    
    def size(self):
        return len(self.heap)

class MaxHeap:
    """
    最大堆实现 (使用负数技巧)
    父节点总是大于子节点
    """
    def __init__(self):
        self.heap = []
    
    def push(self, item):
        heapq.heappush(self.heap, -item)
    
    def pop(self):
        if self.heap:
            return -heapq.heappop(self.heap)
        return None
    
    def peek(self):
        return -self.heap[0] if self.heap else None


# 7. 哈希表 (Hash Table)
# ----------------------------------------------------------------------------
class HashTable:
    """
    哈希表实现 - 使用链地址法处理冲突
    平均情况: 查找、插入、删除 O(1)
    最坏情况: O(n)
    """
    def __init__(self, size=10):
        self.size = size
        self.table = [[] for _ in range(size)]
    
    def _hash(self, key):
        """哈希函数"""
        return hash(key) % self.size
    
    def put(self, key, value):
        """插入键值对"""
        index = self._hash(key)
        for i, (k, v) in enumerate(self.table[index]):
            if k == key:
                self.table[index][i] = (key, value)
                return
        self.table[index].append((key, value))
    
    def get(self, key):
        """获取值"""
        index = self._hash(key)
        for k, v in self.table[index]:
            if k == key:
                return v
        return None
    
    def remove(self, key):
        """删除键值对"""
        index = self._hash(key)
        for i, (k, v) in enumerate(self.table[index]):
            if k == key:
                del self.table[index][i]
                return True
        return False


# 8. 图 (Graph)
# ----------------------------------------------------------------------------
class Graph:
    """
    图的邻接表实现
    支持有向图和无向图
    """
    def __init__(self, directed=False):
        self.graph = {}
        self.directed = directed
    
    def add_vertex(self, vertex):
        """添加顶点"""
        if vertex not in self.graph:
            self.graph[vertex] = []
    
    def add_edge(self, vertex1, vertex2, weight=1):
        """添加边"""
        if vertex1 not in self.graph:
            self.add_vertex(vertex1)
        if vertex2 not in self.graph:
            self.add_vertex(vertex2)
        
        self.graph[vertex1].append((vertex2, weight))
        if not self.directed:
            self.graph[vertex2].append((vertex1, weight))
    
    def get_vertices(self):
        """获取所有顶点"""
        return list(self.graph.keys())
    
    def get_edges(self):
        """获取所有边"""
        edges = []
        for vertex in self.graph:
            for neighbor, weight in self.graph[vertex]:
                if self.directed or (neighbor, vertex, weight) not in edges:
                    edges.append((vertex, neighbor, weight))
        return edges


# ============================================================================
# 第二部分: 排序算法
# ============================================================================

class SortingAlgorithms:
    """排序算法集合"""
    
    @staticmethod
    def bubble_sort(arr):
        """
        冒泡排序
        时间复杂度: O(n²) - 最好O(n), 最坏O(n²)
        空间复杂度: O(1)
        稳定性: 稳定
        原理: 相邻元素两两比较，大的往后移
        """
        n = len(arr)
        for i in range(n):
            swapped = False
            for j in range(0, n - i - 1):
                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
                    swapped = True
            if not swapped:  # 优化：如果没有交换，说明已经有序
                break
        return arr
    
    @staticmethod
    def selection_sort(arr):
        """
        选择排序
        时间复杂度: O(n²)
        空间复杂度: O(1)
        稳定性: 不稳定
        原理: 每次选择最小的元素放到前面
        """
        n = len(arr)
        for i in range(n):
            min_idx = i
            for j in range(i + 1, n):
                if arr[j] < arr[min_idx]:
                    min_idx = j
            arr[i], arr[min_idx] = arr[min_idx], arr[i]
        return arr
    
    @staticmethod
    def insertion_sort(arr):
        """
        插入排序
        时间复杂度: O(n²) - 最好O(n), 最坏O(n²)
        空间复杂度: O(1)
        稳定性: 稳定
        原理: 像打扑克牌一样，将每个元素插入到已排序部分的正确位置
        适用: 小规模数据或基本有序的数据
        """
        for i in range(1, len(arr)):
            key = arr[i]
            j = i - 1
            while j >= 0 and arr[j] > key:
                arr[j + 1] = arr[j]
                j -= 1
            arr[j + 1] = key
        return arr
    
    @staticmethod
    def merge_sort(arr):
        """
        归并排序
        时间复杂度: O(n log n) - 所有情况
        空间复杂度: O(n)
        稳定性: 稳定
        原理: 分治法 - 分割、递归排序、合并
        """
        if len(arr) <= 1:
            return arr
        
        mid = len(arr) // 2
        left = SortingAlgorithms.merge_sort(arr[:mid])
        right = SortingAlgorithms.merge_sort(arr[mid:])
        
        return SortingAlgorithms._merge(left, right)
    
    @staticmethod
    def _merge(left, right):
        """合并两个有序数组"""
        result = []
        i = j = 0
        
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        
        result.extend(left[i:])
        result.extend(right[j:])
        return result
    
    @staticmethod
    def quick_sort(arr):
        """
        快速排序
        时间复杂度: O(n log n) 平均, O(n²) 最坏
        空间复杂度: O(log n)
        稳定性: 不稳定
        原理: 选择基准元素，分区，递归排序
        """
        if len(arr) <= 1:
            return arr
        
        pivot = arr[len(arr) // 2]
        left = [x for x in arr if x < pivot]
        middle = [x for x in arr if x == pivot]
        right = [x for x in arr if x > pivot]
        
        return SortingAlgorithms.quick_sort(left) + middle + SortingAlgorithms.quick_sort(right)
    
    @staticmethod
    def heap_sort(arr):
        """
        堆排序
        时间复杂度: O(n log n) - 所有情况
        空间复杂度: O(1)
        稳定性: 不稳定
        原理: 建立最大堆，依次取出堆顶元素
        """
        def heapify(arr, n, i):
            largest = i
            left = 2 * i + 1
            right = 2 * i + 2
            
            if left < n and arr[left] > arr[largest]:
                largest = left
            if right < n and arr[right] > arr[largest]:
                largest = right
            
            if largest != i:
                arr[i], arr[largest] = arr[largest], arr[i]
                heapify(arr, n, largest)
        
        n = len(arr)
        # 建堆
        for i in range(n // 2 - 1, -1, -1):
            heapify(arr, n, i)
        
        # 排序
        for i in range(n - 1, 0, -1):
            arr[0], arr[i] = arr[i], arr[0]
            heapify(arr, i, 0)
        
        return arr
    
    @staticmethod
    def counting_sort(arr):
        """
        计数排序
        时间复杂度: O(n + k), k是数据范围
        空间复杂度: O(k)
        稳定性: 稳定
        限制: 只适用于非负整数
        原理: 统计每个数出现的次数
        """
        if not arr:
            return arr
        
        max_val = max(arr)
        count = [0] * (max_val + 1)
        
        for num in arr:
            count[num] += 1
        
        result = []
        for num, freq in enumerate(count):
            result.extend([num] * freq)
        
        return result


# ============================================================================
# 第三部分: 搜索算法
# ============================================================================

class SearchAlgorithms:
    """搜索算法集合"""
    
    @staticmethod
    def linear_search(arr, target):
        """
        线性搜索
        时间复杂度: O(n)
        空间复杂度: O(1)
        适用: 无序数组
        """
        for i, num in enumerate(arr):
            if num == target:
                return i
        return -1
    
    @staticmethod
    def binary_search(arr, target):
        """
        二分搜索
        时间复杂度: O(log n)
        空间复杂度: O(1)
        要求: 数组必须有序
        """
        left, right = 0, len(arr) - 1
        
        while left <= right:
            mid = (left + right) // 2
            if arr[mid] == target:
                return mid
            elif arr[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        
        return -1
    
    @staticmethod
    def binary_search_recursive(arr, target, left, right):
        """二分搜索递归版本"""
        if left > right:
            return -1
        
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            return SearchAlgorithms.binary_search_recursive(arr, target, mid + 1, right)
        else:
            return SearchAlgorithms.binary_search_recursive(arr, target, left, mid - 1)
    
    @staticmethod
    def jump_search(arr, target):
        """
        跳跃搜索
        时间复杂度: O(√n)
        空间复杂度: O(1)
        要求: 数组必须有序
        原理: 跳跃式前进，找到区间后线性搜索
        """
        n = len(arr)
        step = int(n ** 0.5)
        prev = 0
        
        while arr[min(step, n) - 1] < target:
            prev = step
            step += int(n ** 0.5)
            if prev >= n:
                return -1
        
        while arr[prev] < target:
            prev += 1
            if prev == min(step, n):
                return -1
        
        if arr[prev] == target:
            return prev
        
        return -1


# ============================================================================
# 第四部分: 图算法
# ============================================================================

class GraphAlgorithms:
    """图算法集合"""
    
    @staticmethod
    def bfs(graph, start):
        """
        广度优先搜索 (BFS)
        时间复杂度: O(V + E), V是顶点数，E是边数
        空间复杂度: O(V)
        应用: 最短路径、层序遍历、连通性检测
        """
        visited = set()
        queue = deque([start])
        result = []
        
        while queue:
            vertex = queue.popleft()
            if vertex not in visited:
                visited.add(vertex)
                result.append(vertex)
                
                for neighbor, _ in graph.graph.get(vertex, []):
                    if neighbor not in visited:
                        queue.append(neighbor)
        
        return result
    
    @staticmethod
    def dfs(graph, start, visited=None):
        """
        深度优先搜索 (DFS)
        时间复杂度: O(V + E)
        空间复杂度: O(V)
        应用: 拓扑排序、环检测、连通分量
        """
        if visited is None:
            visited = set()
        
        visited.add(start)
        result = [start]
        
        for neighbor, _ in graph.graph.get(start, []):
            if neighbor not in visited:
                result.extend(GraphAlgorithms.dfs(graph, neighbor, visited))
        
        return result
    
    @staticmethod
    def dijkstra(graph, start):
        """
        Dijkstra最短路径算法
        时间复杂度: O((V + E) log V) 使用优先队列
        空间复杂度: O(V)
        限制: 不能有负权边
        应用: GPS导航、网络路由
        """
        distances = {vertex: float('inf') for vertex in graph.graph}
        distances[start] = 0
        pq = [(0, start)]
        visited = set()
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            if current in visited:
                continue
            
            visited.add(current)
            
            for neighbor, weight in graph.graph.get(current, []):
                distance = current_dist + weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    heapq.heappush(pq, (distance, neighbor))
        
        return distances
    
    @staticmethod
    def bellman_ford(graph, start):
        """
        Bellman-Ford最短路径算法
        时间复杂度: O(VE)
        空间复杂度: O(V)
        优势: 可以处理负权边，能检测负权环
        """
        distances = {vertex: float('inf') for vertex in graph.graph}
        distances[start] = 0
        
        # 松弛所有边 V-1 次
        for _ in range(len(graph.graph) - 1):
            for vertex in graph.graph:
                for neighbor, weight in graph.graph[vertex]:
                    if distances[vertex] + weight < distances[neighbor]:
                        distances[neighbor] = distances[vertex] + weight
        
        # 检测负权环
        for vertex in graph.graph:
            for neighbor, weight in graph.graph[vertex]:
                if distances[vertex] + weight < distances[neighbor]:
                    return None  # 存在负权环
        
        return distances
    
    @staticmethod
    def topological_sort(graph):
        """
        拓扑排序 (Kahn算法)
        时间复杂度: O(V + E)
        空间复杂度: O(V)
        应用: 任务调度、依赖解析
        要求: 有向无环图(DAG)
        """
        in_degree = {vertex: 0 for vertex in graph.graph}
        
        for vertex in graph.graph:
            for neighbor, _ in graph.graph[vertex]:
                in_degree[neighbor] = in_degree.get(neighbor, 0) + 1
        
        queue = deque([v for v in in_degree if in_degree[v] == 0])
        result = []
        
        while queue:
            vertex = queue.popleft()
            result.append(vertex)
            
            for neighbor, _ in graph.graph.get(vertex, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(result) != len(graph.graph):
            return None  # 存在环
        
        return result


# ============================================================================
# 第五部分: 动态规划
# ============================================================================

class DynamicProgramming:
    """动态规划算法集合"""
    
    @staticmethod
    def fibonacci(n):
        """
        斐波那契数列
        时间复杂度: O(n)
        空间复杂度: O(n) - 可优化到O(1)
        """
        if n <= 1:
            return n
        
        dp = [0] * (n + 1)
        dp[1] = 1
        
        for i in range(2, n + 1):
            dp[i] = dp[i-1] + dp[i-2]
        
        return dp[n]
    
    @staticmethod
    def fibonacci_optimized(n):
        """斐波那契 - 空间优化版"""
        if n <= 1:
            return n
        
        prev, curr = 0, 1
        for _ in range(2, n + 1):
            prev, curr = curr, prev + curr
        
        return curr
    
    @staticmethod
    def knapsack_01(weights, values, capacity):
        """
        0-1背包问题
        时间复杂度: O(nW), n是物品数，W是容量
        空间复杂度: O(nW)
        """
        n = len(weights)
        dp = [[0] * (capacity + 1) for _ in range(n + 1)]
        
        for i in range(1, n + 1):
            for w in range(capacity + 1):
                if weights[i-1] <= w:
                    dp[i][w] = max(
                        dp[i-1][w],
                        dp[i-1][w - weights[i-1]] + values[i-1]
                    )
                else:
                    dp[i][w] = dp[i-1][w]
        
        return dp[n][capacity]
    
    @staticmethod
    def longest_common_subsequence(text1, text2):
        """
        最长公共子序列 (LCS)
        时间复杂度: O(mn)
        空间复杂度: O(mn)
        应用: 文本相似度、版本控制diff
        """
        m, n = len(text1), len(text2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if text1[i-1] == text2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    @staticmethod
    def edit_distance(word1, word2):
        """
        编辑距离 (Levenshtein距离)
        时间复杂度: O(mn)
        空间复杂度: O(mn)
        应用: 拼写检查、DNA序列比对
        """
        m, n = len(word1), len(word2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if word1[i-1] == word2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = min(
                        dp[i-1][j] + 1,    # 删除
                        dp[i][j-1] + 1,    # 插入
                        dp[i-1][j-1] + 1   # 替换
                    )
        
        return dp[m][n]
    
    @staticmethod
    def coin_change(coins, amount):
        """
        硬币找零问题
        时间复杂度: O(amount * len(coins))
        空间复杂度: O(amount)
        """
        dp = [float('inf')] * (amount + 1)
        dp[0] = 0
        
        for i in range(1, amount + 1):
            for coin in coins:
                if i >= coin:
                    dp[i] = min(dp[i], dp[i - coin] + 1)
        
        return dp[amount] if dp[amount] != float('inf') else -1
    
    @staticmethod
    def longest_increasing_subsequence(nums):
        """
        最长递增子序列 (LIS)
        时间复杂度: O(n²) - 这个版本, O(n log n) - 二分优化版
        空间复杂度: O(n)
        """
        if not nums:
            return 0
        
        n = len(nums)
        dp = [1] * n
        
        for i in range(1, n):
            for j in range(i):
                if nums[i] > nums[j]:
                    dp[i] = max(dp[i], dp[j] + 1)
        
        return max(dp)


# ============================================================================
# 第六部分: 贪心算法
# ============================================================================

class GreedyAlgorithms:
    """贪心算法集合"""
    
    @staticmethod
    def activity_selection(start, finish):
        """
        活动选择问题
        时间复杂度: O(n log n)
        原理: 选择最早结束的活动
        """
        activities = sorted(zip(start, finish), key=lambda x: x[1])
        selected = [activities[0]]
        
        for i in range(1, len(activities)):
            if activities[i][0] >= selected[-1][1]:
                selected.append(activities[i])
        
        return selected
    
    @staticmethod
    def fractional_knapsack(weights, values, capacity):
        """
        分数背包问题
        时间复杂度: O(n log n)
        区别于0-1背包: 可以取物品的一部分
        """
        items = [(v/w, w, v) for v, w in zip(values, weights)]
        items.sort(reverse=True)
        
        total_value = 0
        for ratio, weight, value in items:
            if capacity >= weight:
                capacity -= weight
                total_value += value
            else:
                total_value += ratio * capacity
                break
        
        return total_value
    
    @staticmethod
    def huffman_coding(freq):
        """
        霍夫曼编码
        时间复杂度: O(n log n)
        应用: 数据压缩
        """
        heap = [[weight, [symbol, ""]] for symbol, weight in freq.items()]
        heapq.heapify(heap)
        
        while len(heap) > 1:
            lo = heapq.heappop(heap)
            hi = heapq.heappop(heap)
            
            for pair in lo[1:]:
                pair[1] = '0' + pair[1]
            for pair in hi[1:]:
                pair[1] = '1' + pair[1]
            
            heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
        
        return sorted(heap[0][1:], key=lambda p: (len(p[-1]), p))


# ============================================================================
# 第七部分: 回溯算法
# ============================================================================

class BacktrackingAlgorithms:
    """回溯算法集合"""
    
    @staticmethod
    def permutations(nums):
        """
        全排列
        时间复杂度: O(n!)
        空间复杂度: O(n)
        """
        result = []
        
        def backtrack(path, remaining):
            if not remaining:
                result.append(path[:])
                return
            
            for i in range(len(remaining)):
                path.append(remaining[i])
                backtrack(path, remaining[:i] + remaining[i+1:])
                path.pop()
        
        backtrack([], nums)
        return result
    
    @staticmethod
    def combinations(n, k):
        """
        组合问题: 从1到n中选k个数
        时间复杂度: O(C(n,k))
        """
        result = []
        
        def backtrack(start, path):
            if len(path) == k:
                result.append(path[:])
                return
            
            for i in range(start, n + 1):
                path.append(i)
                backtrack(i + 1, path)
                path.pop()
        
        backtrack(1, [])
        return result
    
    @staticmethod
    def n_queens(n):
        """
        N皇后问题
        时间复杂度: O(n!)
        应用: 经典回溯问题
        """
        result = []
        board = [['.'] * n for _ in range(n)]
        
        def is_valid(row, col):
            # 检查列
            for i in range(row):
                if board[i][col] == 'Q':
                    return False
            
            # 检查左上对角线
            i, j = row - 1, col - 1
            while i >= 0 and j >= 0:
                if board[i][j] == 'Q':
                    return False
                i -= 1
                j -= 1
            
            # 检查右上对角线
            i, j = row - 1, col + 1
            while i >= 0 and j < n:
                if board[i][j] == 'Q':
                    return False
                i -= 1
                j += 1
            
            return True
        
        def backtrack(row):
            if row == n:
                result.append([''.join(row) for row in board])
                return
            
            for col in range(n):
                if is_valid(row, col):
                    board[row][col] = 'Q'
                    backtrack(row + 1)
                    board[row][col] = '.'
        
        backtrack(0)
        return result
    
    @staticmethod
    def sudoku_solver(board):
        """
        数独求解器
        时间复杂度: O(9^(n*n))
        """
        def is_valid(row, col, num):
            # 检查行
            if num in board[row]:
                return False
            
            # 检查列
            if num in [board[i][col] for i in range(9)]:
                return False
            
            # 检查3x3方格
            start_row, start_col = 3 * (row // 3), 3 * (col // 3)
            for i in range(start_row, start_row + 3):
                for j in range(start_col, start_col + 3):
                    if board[i][j] == num:
                        return False
            
            return True
        
        def solve():
            for i in range(9):
                for j in range(9):
                    if board[i][j] == '.':
                        for num in '123456789':
                            if is_valid(i, j, num):
                                board[i][j] = num
                                if solve():
                                    return True
                                board[i][j] = '.'
                        return False
            return True
        
        solve()
        return board


# ============================================================================
# 第八部分: 字符串算法
# ============================================================================

class StringAlgorithms:
    """字符串算法集合"""
    
    @staticmethod
    def kmp_search(text, pattern):
        """
        KMP字符串匹配算法
        时间复杂度: O(n + m)
        空间复杂度: O(m)
        优势: 避免重复比较
        """
        def compute_lps(pattern):
            """计算最长前缀后缀数组"""
            m = len(pattern)
            lps = [0] * m
            length = 0
            i = 1
            
            while i < m:
                if pattern[i] == pattern[length]:
                    length += 1
                    lps[i] = length
                    i += 1
                else:
                    if length != 0:
                        length = lps[length - 1]
                    else:
                        lps[i] = 0
                        i += 1
            
            return lps
        
        n, m = len(text), len(pattern)
        lps = compute_lps(pattern)
        result = []
        
        i = j = 0
        while i < n:
            if text[i] == pattern[j]:
                i += 1
                j += 1
            
            if j == m:
                result.append(i - j)
                j = lps[j - 1]
            elif i < n and text[i] != pattern[j]:
                if j != 0:
                    j = lps[j - 1]
                else:
                    i += 1
        
        return result
    
    @staticmethod
    def rabin_karp(text, pattern):
        """
        Rabin-Karp字符串匹配算法
        时间复杂度: O(n + m) 平均, O(nm) 最坏
        原理: 使用哈希值快速比较
        """
        n, m = len(text), len(pattern)
        d = 256  # 字符集大小
        q = 101  # 质数
        
        h = pow(d, m - 1, q)
        p = t = 0
        result = []
        
        # 计算模式串和文本第一个窗口的哈希值
        for i in range(m):
            p = (d * p + ord(pattern[i])) % q
            t = (d * t + ord(text[i])) % q
        
        # 滑动窗口
        for i in range(n - m + 1):
            if p == t:
                if text[i:i+m] == pattern:
                    result.append(i)
            
            if i < n - m:
                t = (d * (t - ord(text[i]) * h) + ord(text[i + m])) % q
                if t < 0:
                    t += q
        
        return result
    
    @staticmethod
    def longest_palindromic_substring(s):
        """
        最长回文子串
        时间复杂度: O(n²)
        空间复杂度: O(1)
        """
        def expand_around_center(left, right):
            while left >= 0 and right < len(s) and s[left] == s[right]:
                left -= 1
                right += 1
            return right - left - 1
        
        if not s:
            return ""
        
        start = end = 0
        for i in range(len(s)):
            len1 = expand_around_center(i, i)      # 奇数长度
            len2 = expand_around_center(i, i + 1)  # 偶数长度
            max_len = max(len1, len2)
            
            if max_len > end - start:
                start = i - (max_len - 1) // 2
                end = i + max_len // 2
        
        return s[start:end + 1]


# ============================================================================
# 使用示例
# ============================================================================

def demonstrate_algorithms():
    """演示各种算法的使用"""
    
    print("="*60)
    print("算法与数据结构演示")
    print("="*60)
    
    # 1. 链表演示
    print("\n【1. 链表】")
    ll = LinkedList()
    ll.append(1)
    ll.append(2)
    ll.append(3)
    ll.prepend(0)
    print(f"链表内容: {ll.display()}")
    
    # 2. 栈演示
    print("\n【2. 栈 - LIFO】")
    stack = Stack()
    for i in [1, 2, 3]:
        stack.push(i)
    print(f"栈顶元素: {stack.peek()}")
    print(f"弹出: {stack.pop()}")
    
    # 3. 队列演示
    print("\n【3. 队列 - FIFO】")
    queue = Queue()
    for i in [1, 2, 3]:
        queue.enqueue(i)
    print(f"队首元素: {queue.front()}")
    print(f"出队: {queue.dequeue()}")
    
    # 4. 二叉搜索树演示
    print("\n【4. 二叉搜索树】")
    bst = BST()
    for val in [5, 3, 7, 1, 9]:
        bst.insert(val)
    print(f"查找7: {'找到' if bst.search(7) else '未找到'}")
    
    # 5. 排序算法演示
    print("\n【5. 排序算法】")
    arr = [64, 34, 25, 12, 22, 11, 90]
    print(f"原数组: {arr}")
    print(f"快速排序: {SortingAlgorithms.quick_sort(arr.copy())}")
    print(f"归并排序: {SortingAlgorithms.merge_sort(arr.copy())}")
    
    # 6. 搜索算法演示
    print("\n【6. 搜索算法】")
    sorted_arr = [1, 3, 5, 7, 9, 11, 13, 15]
    target = 7
    print(f"数组: {sorted_arr}, 查找: {target}")
    print(f"二分搜索结果索引: {SearchAlgorithms.binary_search(sorted_arr, target)}")
    
    # 7. 图算法演示
    print("\n【7. 图算法】")
    g = Graph()
    edges = [('A', 'B', 1), ('A', 'C', 4), ('B', 'C', 2), ('B', 'D', 5), ('C', 'D', 1)]
    for v1, v2, w in edges:
        g.add_edge(v1, v2, w)
    print(f"BFS遍历: {GraphAlgorithms.bfs(g, 'A')}")
    print(f"最短路径(从A): {GraphAlgorithms.dijkstra(g, 'A')}")
    
    # 8. 动态规划演示
    print("\n【8. 动态规划】")
    print(f"斐波那契(10): {DynamicProgramming.fibonacci(10)}")
    print(f"LCS('ABCDGH', 'AEDFHR'): {DynamicProgramming.longest_common_subsequence('ABCDGH', 'AEDFHR')}")
    print(f"硬币找零([1,2,5], 11): {DynamicProgramming.coin_change([1, 2, 5], 11)}")
    
    # 9. 回溯算法演示
    print("\n【9. 回溯算法】")
    print(f"全排列[1,2,3]: {BacktrackingAlgorithms.permutations([1, 2, 3])[:3]}... (前3个)")
    print(f"4皇后问题解的数量: {len(BacktrackingAlgorithms.n_queens(4))}")
    
    # 10. 字符串算法演示
    print("\n【10. 字符串算法】")
    text = "ABABCABABA"
    pattern = "ABA"
    print(f"文本: {text}")
    print(f"模式: {pattern}")
    print(f"KMP匹配位置: {StringAlgorithms.kmp_search(text, pattern)}")
    print(f"最长回文子串('babad'): {StringAlgorithms.longest_palindromic_substring('babad')}")

# 运行演示
if __name__ == "__main__":
    demonstrate_algorithms()