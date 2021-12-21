# cimaclub-dl
cimaclub cli downloader

# requirements :  
``pip install beautifulsoup4``
``pip install requests``
# using docker
now you can use docker to run this script

all you need is to have docker installed on your machine and run the following commands to get the cimaclub image and run it

* ``docker build -t cimaclub .`` to build the image
* ``docker run -it -v absolute_path_to_the_location_of_fetched_links:/app/results --name cimaclub cimaclub`` to run the image

and inorder to use it again do the following command :
* ``docker start cimaclub`` to start the container
* ``docker exec -it cimaclub`` to enter the container
# use:  
in order to use this script all you need is to go to the folder cimaclub-dl  
and run ``python index.py``  
then you enter the title of the movie / series you are looking for  
  
![execution image](https://user-images.githubusercontent.com/74828398/141826898-4daabf29-cc3b-4879-b8b6-d5c083610ed8.png)  
  
after that, you choose the episode/movie you want, and the quality of the video.  
And you will be able to either save the links in a txt file, or start downloading by opening the links in the default browser
