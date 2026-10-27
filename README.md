Running Program:
  # Create virtual env
  python -m venv .venv
  # activate virtual environment
  source ./bin/activate
  # install dependencies
  pip install
  python ./src/main.py + args

usage: main.py [-h] [--transform_algorithm TRANSFORM_ALGORITHM] [--ransac_threshold RANSAC_THRESHOLD] [--ransac_max_iterations RANSAC_MAX_ITERATIONS] [--neighbor_threshold NEIGHBOR_THRESHOLD]
               [--debug_draw DEBUG_DRAW] [--show_outlier SHOW_OUTLIER] [--use_mean USE_MEAN]
               image_path

output: new_image.jpg in repository's directory

Feature Matching Evaluation:
  The image pair that I used to compare nearest-neighbor ratios was the DVD. The main reason why I chose DVD was because it has a high median of reprojection   
  errors before performing ransac. This is important because if the median of reprojection errors before performing ransac is low enough to basically be the 
  reprojection after performing ransac there is no use in further tightening the matching threshold because the outcome will be near identical. 

  DVD reprojection median before after ransac: || neighbor_threshold = 0.75
    before: 30.05
    after: 1.0
  uttower reprojection median || neighbor_threshold = 0.75
    before: 0.51
    after: 0.47

  DVD reprojection median before after ransac: || neighbor_threshold = 0.4
    before: 0.46
    after: 0.44
  uttower reprojection median || neighbor_threshold = 0.4
    before: 0.40
    after: 0.40

  we can see that the outcome of tightening the threshold for the DVD pair made a far greater change than it did for the uttower pair, as changing the threshold 
  of the uttower pair.

  Total_matches: 1811
  Here is the dvd pair with a threshold of 0.75
  kept_matches = 221
  ![./images/high_neighbor_debug_dvd]

  Here is the dvd pair with a threshold of 0.4
  kept_matches = 14
  ![./images/loww_neighbor_debug_dvd]

  Here is the dvd pair with a threshold of 0.35

  While giving a look at the dvd matches with a threshold of 0.75 it didn't take me long to find inconsistent pixels which didn't come as a surprise as
  half of the errors were at least 30 pixels away. The most egregious error I found was a match on the circular border of the purple book's logo right underneath 
  the top right black square of text on the left picture. On the right picture the matched point can be found on the seam of the scratched wood, right underneath
  the bottom right corner of the same book.

  The tradeoff we experience when lowering the neighbor threshold is that we keep keypoint matches that are more unique than the next best match but in return we 
  may filter out perfectly good points if the neighbor_threshold is too low. 

  RANSAC Evaluation:
    Matches: 221
    inlier_cnt: 38
    outlier_cnt: 183
    mean reprojection before RANSAC: 126.4
    mean reprojection after RANSAC: 1.42

    The reprojection error after RANSAC are the points presented in this photo

    ![./images/ransac_inlier]

    The reprojection error before RANSAC is the union of the photo above and the one below

    ![./images/ransac_outlier]
  
  Affine vs Homography:
    ![./images/affine_dvd.jpg]
      inlier_cnt: 8
      reprojection_error: before=15.5, after=0.58
    ![./images/homography_dvd.jpg]
      inlier_cnt: 11
      reprojection_error: before=4.7, after=0.48
    
    The first image shows us the affine transform while the second image shows us the homography transform

    This image pair shows the largest visual difference between a Affine and Perspective transform. The reason why the Affine looks so much worse
    than the perspective transform is because the perspective of the camera changed drastically enough that the vanishing point of both photos were
    on completely opposite end of each other. Affine simply does not have the flexibility to change the vanishing point of an image. Perspective
    Transform does not have this issue, as it has 8 degrees of freedom compared to Affine's 6

    The reprojection error after RANSAC in the affine transform surprised me, as it looked shockingly low for how bad the output looked. When looking at the
    inliers I soon realized why. The inliers are clustered together and so the result was biased in making sure that the cluster was matched as best as possible
    and since the points were close to one another the vanishing point was not accentuated enough to make a difference.


    uttower Affine:
      inlier_cnt: 120
      reprojection_error: before=2.87, after=1.03
    uttower Homography:
      inlier_cnt: 170
      reprojection_error: before=0.67, after=0.50
    
    unsurprisingly, the homography outperforms the affine transform but the affine transform still performed really well!
    
    the uttower pair has similar vanishing points which allows the affine stitch much more realistically than the dvd pair.
    One pattern that I noticed, however, was that affine's inliers, once again, tended to cluster together a lot more than 
    the Homography transform.
    

  
    

  


