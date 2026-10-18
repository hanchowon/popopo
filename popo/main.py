from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Binary Search Tree API Server")

# ==========================================
# 1. CORS(Cross-Origin Resource Sharing) 설정
# GAS(Google Apps Script) 도메인에서의 Cross-Origin 요청 허용
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 Origin의 접근 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST, OPTIONS 등)
    allow_headers=["*"],  # 모든 헤더 허용
)


# ==========================================
# 2. 이진 검색 트리 (BST) 자료구조 클래스 정의
# ==========================================
class Node:

  def __init__(
      self,
      key: Any,
      value: Any = None,
      left: Optional["Node"] = None,
      right: Optional["Node"] = None,
  ):
    """트리의 단일 노드 클래스

    :param key: 비교 가능한 키 값 (숫자 또는 문자열)
    :param value: 노드가 저장할 데이터 값
    :param left: 왼쪽 자식 노드 포인터
    :param right: 오른쪽 자식 노드 포인터
    """
    self.key = key
    self.value = value
    self.left = left
    self.right = right


class BinarySearchTree:

  def __init__(self):
    """이진 검색 트리 초기화 (init)"""
    self.root: Optional[Node] = None

  def search(self, key: Any) -> Optional[Any]:
    """키를 이용해 트리에서 노드의 값을 검색 (search)

    :param key: 찾고자 하는 키
    :return: 찾으면 노드의 value, 없으면 None
    """
    p = self.root
    while p is not None:
      if key == p.key:
        return p.value
      elif key < p.key:
        p = p.left
      else:
        p = p.right
    return None

  def add(self, key: Any, value: Any = None) -> bool:
    """트리에 새로운 (key, value) 노드 추가 (add)

    :param key: 추가할 키
    :param value: 추가할 값
    :return: 새로 추가되었으면 True, 기존 키의 값이 업데이트되었으면 False
    """

    def _add_node(node: Optional[Node], key: Any, value: Any) -> Node:
      if node is None:
        return Node(key, value)
      if key == node.key:
        node.value = value  # 이미 키가 존재하는 경우 값 업데이트
      elif key < node.key:
        node.left = _add_node(node.left, key, value)
      else:
        node.right = _add_node(node.right, key, value)
      return node

    existed = self.search(key) is not None
    self.root = _add_node(self.root, key, value)
    return not existed

  def remove(self, key: Any) -> bool:
    """트리에서 특정 키를 가진 노드를 삭제 (remove)

    :param key: 삭제할 키
    :return: 삭제 성공 시 True, 키가 없으면 False
    """

    def _min_value_node(node: Node) -> Node:
      current = node
      while current.left is not None:
        current = current.left
      return current

    def _delete_node(
        node: Optional[Node], key: Any
    ) -> tuple[Optional[Node], bool]:
      if node is None:
        return None, False

      deleted = False
      if key < node.key:
        node.left, deleted = _delete_node(node.left, key)
      elif key > node.key:
        node.right, deleted = _delete_node(node.right, key)
      else:
        deleted = True
        # 자식 노드가 없거나 1개인 경우
        if node.left is None:
          return node.right, True
        elif node.right is None:
          return node.left, True

        # 자식 노드가 2개인 경우: 오른쪽 서브트리의 최소값 노드(후계자)를 찾아 대체
        temp = _min_value_node(node.right)
        node.key = temp.key
        node.value = temp.value
        node.right, _ = _delete_node(node.right, temp.key)

      return node, deleted

    self.root, is_deleted = _delete_node(self.root, key)
    return is_deleted

  def min_key(self) -> Optional[Any]:
    """트리에서 가장 작은 키 반환 (min_key) - 가장 왼쪽 노드"""
    if self.root is None:
      return None
    p = self.root
    while p.left is not None:
      p = p.left
    return p.key

  def max_key(self) -> Optional[Any]:
    """트리에서 가장 큰 키 반환 (max_key) - 가장 오른쪽 노드"""
    if self.root is None:
      return None
    p = self.root
    while p.right is not None:
      p = p.right
    return p.key

  def dump(self) -> Optional[Dict[str, Any]]:
    """트리 전체 구조를 JSON 응답/시각화용 중첩 Dict로 변환 (dump)"""

    def _serialize(node: Optional[Node]) -> Optional[Dict[str, Any]]:
      if node is None:
        return None
      return {
          "key": node.key,
          "value": node.value,
          "left": _serialize(node.left),
          "right": _serialize(node.right),
      }

    return _serialize(self.root)


# 메모리 상에서 구동될 전역 이진 검색 트리 인스턴스
global_bst: Optional[BinarySearchTree] = None


# ==========================================
# 3. Pydantic 요청 데이터 모델
# ==========================================
class ItemRequest(BaseModel):
  key: Any
  value: Optional[Any] = None


# ==========================================
# 4. API Endpoints
# ==========================================
@app.get("/")
def health_check():
  """서버 상시 동작 확인용 헬스체크"""
  return {"status": "ok", "message": "BST Server is running."}


@app.post("/init")
def api_init():
  """이진 검색 트리 초기화 (init)"""
  global global_bst
  global_bst = BinarySearchTree()
  return {
      "status": "success",
      "message": "Binary Search Tree initialized successfully.",
  }


def _check_bst_initialized():
  if global_bst is None:
    raise HTTPException(
        status_code=400, detail="BST is not initialized. Call /init first."
    )


def _parse_key(key: Any) -> Any:
  """키가 숫자형인 경우 int로 자동 변환"""
  try:
    return int(key)
  except (ValueError, TypeError):
    return key


@app.post("/add")
def api_add(req: ItemRequest):
  """노드 추가/업데이트 (add)"""
  global global_bst
  if global_bst is None:
    global_bst = BinarySearchTree()

  key = _parse_key(req.key)
  val = req.value if req.value is not None else f"Val-{key}"
  is_new = global_bst.add(key, val)

  return {
      "status": "success",
      "action": "added" if is_new else "updated",
      "key": key,
      "value": val,
  }


@app.post("/search")
def api_search(req: ItemRequest):
  """노드 검색 (search)"""
  _check_bst_initialized()
  key = _parse_key(req.key)
  val = global_bst.search(key)

  return {"found": val is not None, "key": key, "value": val}


@app.post("/remove")
def api_remove(req: ItemRequest):
  """노드 삭제 (remove)"""
  _check_bst_initialized()
  key = _parse_key(req.key)
  success = global_bst.remove(key)

  if not success:
    raise HTTPException(
        status_code=404, detail=f"Key '{key}' not found in tree."
    )

  return {
      "status": "success",
      "message": f"Key '{key}' successfully removed.",
      "key": key,
  }


@app.get("/dump")
def api_dump():
  """트리 전체 구조 직렬화 반환 (dump)"""
  _check_bst_initialized()
  return {"status": "success", "tree": global_bst.dump()}


@app.get("/range")
def api_range():
  """트리 내 최소키 및 최대키 범위 반환 (min_key, max_key)"""
  _check_bst_initialized()
  min_k = global_bst.min_key()
  max_k = global_bst.max_key()

  return {"status": "success", "min_key": min_k, "max_key": max_k}
