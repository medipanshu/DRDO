from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QMovie
import sys

app = QApplication(sys.argv)
label = QLabel()
movie = QMovie("Assets/Gear_Loader_dark.gif")  # Use exact path

label.setMovie(movie)
label.setFixedSize(100, 100)
label.show()
movie.start()

sys.exit(app.exec_())
