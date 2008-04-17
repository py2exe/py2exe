import sys
import time

import EasyDialogs

if __name__ == "__main__":
    progressBar = EasyDialogs.ProgressBar('Testing py2exe', 100, 'Testing, testing, 1-2-3...')
    for i in range(100):
        time.sleep(0.001)
        progressBar.inc()

    print progressBar.curval
    sys.exit(progressBar.curval)
