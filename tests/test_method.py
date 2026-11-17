"""Small hand-checkable cases for missingness and grouped event semantics."""
import unittest,sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/analysis'))
from io_records import parse_cell
from mine_support import index,metric

class MethodTests(unittest.TestCase):
    def test_unknown_and_observed_empty_are_distinct(self):
        self.assertIsNone(parse_cell('未记录'))
        self.assertEqual(parse_cell('[]'),frozenset())
        self.assertEqual(parse_cell(' 黄铁矿 ; 黄铁矿 '),frozenset(['黄铁矿']))

    def test_same_feature_items_are_one_joint_event(self):
        # Three jointly observed groups; the fourth is unknown for feature B.
        rows=[[frozenset(['a','b']),frozenset(['x'])],
              [frozenset(['a','b']),frozenset()],
              [frozenset(['a']),frozenset()],
              [frozenset(['a','b']),None]]
        obs,items=index(rows)
        p=metric(((0,'a'),(0,'b'),(1,'x')),obs,items,4)
        self.assertEqual(p['valid_n'],3);self.assertEqual(p['count'],1)
        self.assertEqual(p['group_counts'],{0:2,1:1})
        self.assertAlmostEqual(p['group_lift'],1.5)
        self.assertAlmostEqual(p['evidence'],math.log(1.5)/4)

if __name__=='__main__':unittest.main()
