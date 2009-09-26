#!/usr/bin/env python

import unittest
import skeleton

class testSkeleton(unittest.TestCase):
    """
    A test class for the Skeleton module.
    """

    def setUp(self):
        """
        set up data used in the tests.
        setUp is called before each test function execution.
        """
        pass        
        
    def tearDown(self):
        """
        Cleanup after all test are run
        """
        pass                


    def testOne(self):

        self.assertEqual(1, 1)


    def testTwo(self):

        self.assertEqual(2, 2)


    def testThree(self):

        self.assertEqual(3, 3)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testSkeleton))
    return suite
    

if __name__ == '__main__':    
    unittest.TextTestRunner(verbosity=2).run(suite())

