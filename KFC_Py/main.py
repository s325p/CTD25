import cv2
import logging
from GameFactory import create_game
from GraphicsFactory import ImgFactory

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    game = create_game("pieces", ImgFactory())
    game.run()


    # Load and resize start image to match game board size
    # img = cv2.imread("pic/start.png")
    # if img is not None:
    #     # Game board dimensions: 768px (board) + 600px (side panels) = 1368px width, 768px height
    #     game_width = 768 + (2 * 300)  # board + 2 side panels
    #     game_height = 768  # board height
    #     img_resized = cv2.resize(img, (game_width, game_height))
    #     cv2.imshow("Chess Game", img_resized)
    # else:
    #     print("Start image not found!")
    
    # cv2.waitKey(3000)   
    # cv2.destroyAllWindows() 



