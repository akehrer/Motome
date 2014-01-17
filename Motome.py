__author__ = 'Aaron Kehrer'

# Import the needed ZODB objects
import transaction
from ZODB.FileStorage import FileStorage
from ZODB.DB import DB
from BTrees.OOBTree import OOBTree

from Motome import main

if __name__ == '__main__':
    main()