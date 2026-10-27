from __future__ import print_function
from pathlib import Path
import numpy as np
import cv2
import matplotlib
import argparse
import sys
import random
import colorsys
from PIL import Image

matplotlib.use('module://kitcat');
import matplotlib.pyplot as plt


def hsv2rgb(h,s,v):
    return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h,s,v))

def computePointHomography(M, points):
    points = np.append(points, [1])
    out = None
    out = np.dot(M, points)
    return np.array([out[0]/out[2],out[1]/out[2]])

def sift_match_align(l_img, l_gray, r_img, r_gray, kept_matches, align, neighbor_threshold, ransac_threshold, debug, show_outlier, use_mean, ransac_iterations):
    sift = cv2.SIFT_create()

    l_kp, l_des = sift.detectAndCompute(l_gray, None)
    r_kp, r_des = sift.detectAndCompute(r_gray, None)

    bf = cv2.BFMatcher()
    matches = bf.knnMatch(l_des, r_des, k=2)

    good_matches = []
    for m,n in matches:
        if m.distance < neighbor_threshold*n.distance:
            good_matches.append(m)

    
    kept_matches = good_matches
    src_pts = np.float32([ l_kp[m.queryIdx].pt for m in good_matches ]).reshape(-1,1,2)
    des_pts = np.float32([ r_kp[m.trainIdx].pt for m in good_matches ]).reshape(-1,1,2)

    (r_h, r_w) = r_img.shape[:2]
    (l_h, l_w) = l_img.shape[:2]

    if debug == 1:
        print("neighbor_threshold:", neighbor_threshold)
        print("kept_matches:", len(kept_matches))
        print("matches:", len(matches))

    if align == 1:
        M, mask = cv2.findHomography(des_pts, src_pts, cv2.RANSAC, ransac_threshold, maxIters=ransac_iterations)
    else:
        M, mask = cv2.estimateAffine2D(des_pts, src_pts, method=cv2.RANSAC, ransacReprojThreshold=ransac_threshold, maxIters=ransac_iterations)
        M = np.append(M, [[0,0,1]], axis=0)

    if debug == 2 or debug == 1:
        max_h = l_h if l_h > r_h else r_h
        random.seed()

        debug_img = np.zeros((max_h, l_img.shape[1] + r_img.shape[1], l_img.shape[2]), dtype=np.uint8)
        debug_img[0:l_h, 0:l_w, 0:4] = l_img
        debug_img[0:r_h, l_w:, 0:4] = r_img
        
        inlier_cnt = 0;
        reproj_error = np.zeros((len(mask)), dtype=np.float32)
        after_mask = np.zeros((len(mask)), dtype=int)
        for inlier in range(len(mask)):
            color = hsv2rgb(random.random(), 1.0, 0.7)
            reproj_error[inlier] = np.sqrt(np.sum((computePointHomography(M, des_pts[inlier, 0]) - src_pts[inlier, 0]) ** 2, axis=-1))
            if mask[inlier] == 1:
                inlier_cnt += 1;
            else:
                after_mask[inlier] = 1
            if mask[inlier] == 1 and (show_outlier == 0 or debug == 1):
                cv2.circle(debug_img, [int(des_pts[inlier][0][0])+l_w, int(des_pts[inlier][0][1])], 5, color, 4)
                cv2.circle(debug_img, [int(src_pts[inlier][0][0]), int(src_pts[inlier][0][1])], 5, color, 4)
            elif mask[inlier] == 0 and (show_outlier == 1 or debug == 1):
                cv2.circle(debug_img, [int(des_pts[inlier][0][0])+l_w, int(des_pts[inlier][0][1])], 5, color, 4)
                cv2.circle(debug_img, [int(src_pts[inlier][0][0]), int(src_pts[inlier][0][1])], 5, color, 4)
        # print(reproj_error)
        if use_mean:
            before_error = np.sum(reproj_error) / len(reproj_error)
            after_error_mask = np.ma.array(reproj_error, mask=after_mask)
            after_error = after_error_mask.sum() / inlier_cnt
            print("mean:")
            print("Reprojection Error before RANSAC:", before_error)
            print("Reprojection Error after RANSAC:", after_error)
        else:
            before_error = np.median(reproj_error)
            after_error_mask = np.ma.array(reproj_error, mask=after_mask)
            after_error = np.ma.median(after_error_mask)
            print("median:")
            print("Reprojection Error before RANSAC:", before_error)
            print("Reprojection Error after RANSAC:", after_error)
            
        print("inlier_cnt:", inlier_cnt)
        print("outlier_cnt:", len(mask) - inlier_cnt)
        print("match_cnt:", len(mask))
        print("")


        return debug_img


    img_aligned = cv2.cvtColor(cv2.warpPerspective(r_img, M, (l_w + r_w, l_h)), cv2.COLOR_RGB2RGBA)
    l_img_a = cv2.cvtColor(l_img, cv2.COLOR_RGB2RGBA)
    l_img_aligned = np.zeros(img_aligned.shape, dtype=np.uint8)
    l_img_aligned[0:l_h, 0:l_w, 0:4] = l_img_a


    leftmost_pixel_j = l_w;
    for i in range(img_aligned.shape[0]):
        for j in range(img_aligned.shape[1]):
            if not img_aligned[i][j][:3].any():
                img_aligned[i][j][3] = 0
            elif leftmost_pixel_j > j:
                leftmost_pixel_j = j

    mid = (leftmost_pixel_j + l_w) // 2
    blendSize = mid - leftmost_pixel_j if mid - leftmost_pixel_j > l_w - mid else l_w - mid

    img_aligned[0:l_h, 0:mid - blendSize+1] = l_img_aligned[0:l_h, 0:mid - blendSize+1]
    

    img_aligned[0:l_h, mid] = cv2.addWeighted(img_aligned[0:l_h, mid], 0.5, l_img_aligned[0:l_h, mid], 0.5, 0)
    

    for i in range(0,blendSize+1):
        for j in range(l_h):
            if img_aligned[j][mid - i][3] != 255:
                img_aligned[j][mid - i] = l_img_aligned[j][mid - i]
            if img_aligned[j][mid + i][3] != 255:
                img_aligned[j][mid + i] = l_img_aligned[j][mid + i]

        blendValueLeft = (i / blendSize)*0.50 + 0.50
        blendValueRight = 0.50 - (i / blendSize)*0.50
        
        img_aligned[0:l_h, mid - i] = cv2.addWeighted(img_aligned[0:l_h, mid-i], 1-blendValueLeft, l_img_aligned[0:l_h, mid-i], blendValueLeft, 0)
        img_aligned[0:l_h, mid + i] = cv2.addWeighted(img_aligned[0:l_h, mid+i], 1-blendValueRight, l_img_aligned[0:l_h, mid+i], blendValueRight, 0)

    
    img_aligned = cv2.cvtColor(img_aligned, cv2.COLOR_RGBA2RGB)
    img_cropped = None 

    for i in range(len(img_aligned[0])-1, 0, -1):
        isPhoto = False
        for j in range(len(img_aligned)):
            if np.any(img_aligned[j][i]):
                isPhoto = True
        if isPhoto == True:
            img_cropped = img_aligned[0:, 0:i, 0:];
            break;
    return img_cropped


def main():
    parser = argparse.ArgumentParser(
        description="panorama stitcher"
    )

    parser.add_argument('image_path')
    parser.add_argument('--transform_algorithm', help="Affine Transform = 0 | Homography Transform = 1", default=0, type=int)
    parser.add_argument('--ransac_threshold', help="Maximum reprojection error to consider a point as an inlier, default 3.0", default=3.0, type=float)
    parser.add_argument('--ransac_max_iterations', help="Maximum iterations for ransac", default=2000, type=int)
    parser.add_argument('--neighbor_threshold', help="threshold for nearest neighbor, default=0.75", default=0.75, type=float)
    parser.add_argument('--debug_draw', help="outputs images for debugging matches Matches=1 | RANSAC=2", default=0, type=int)
    parser.add_argument('--show_outlier', help="shows outliers for debug_draw only when it is set to 2", default=0, type=int)
    parser.add_argument('--use_mean', help="set to 1 if you want reprojection error to be calculated with mean, 0 for median", default=1, type=int)
    args = parser.parse_args()

    dir_path = Path(args.image_path)

    images = list(map(cv2.imread, list(str(file) for file in dir_path.iterdir() if file.is_file)))
    images.reverse()

    images_g = list(map(lambda x:cv2.cvtColor(x, cv2.COLOR_BGR2GRAY), images))

    # test = list(str(file) for file in dir_path.iterdir() if file.is_file)
    # print(test)

    if len(images) > 2 and args.debug_draw:
        print("Can only draw matches for two images")
        sys.exit()

    if len(images) == 1:
        print("not enough images");
        sys.exit()

    if len(images) == 2:
        out = sift_match_align(images[0], images_g[0], images[1], images_g[1], 4, args.transform_algorithm, args.neighbor_threshold,  args.ransac_threshold, args.debug_draw, args.show_outlier, args.use_mean, args.ransac_max_iterations)
    else:
        out = sift_match_align(images[0], images_g[0], images[1], images_g[1], 4, args.transform_algorithm, args.neighbor_threshold, args.ransac_threshold, 0, args.show_outlier, args.use_mean, args.ransac_max_iterations)
        out_g = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)
        for i in range(2, len(images)):
            print(len(out.shape))
            out = sift_match_align(out, out_g, images[i], images_g[i], 4, args.transform_algorithm, args.neighbor_threshold, args.ransac_threshold, 0, args.show_outlier, args.use_mean, args.ransac_max_iterations)
            out_g = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)

    # out = sift_match_align(left_img, left_img_g, right_img, right_img_g, 3, 1, 0)
    # out_g = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)
    #
    # out = sift_match_align(out, out_g, test_img, test_g, 3, 1, 1)

    cv2.imwrite("new_image.jpg", out)
    plt.imshow(out)
    plt.show()


if __name__ == '__main__':
    main()
