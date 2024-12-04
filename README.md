# SILAM-plot Slim Silam suite


Adds an extract from SILAM global animation to a web site


## Setup 

1. Get needed dependencies: python3, grads, imagemagick, and some web server unless you already have one. 

2. Checkut a needed branch (e.g. KGZ-khm), create your own branch and switch to it.

3. Add your contact e-mail to the `environment` file. This will be used to notify you when we decide 
   to change something in the data and/or access procedure.

4. Configure your web server to share the content of `/var/www/html` or change the path in `make_pictures.sh`
  to the location available for your web server.

5. Try `runit.sh`.

6. Add to the cronjob something like

``
    1 08 * * * /bin/bash ${HOME}/SILAM-plot/runit.sh > ${HOME}/SILAM-plot/logs/runit`date +\%Y\%m\%d_\%H\%M`.log 2>&1
``

 or wjatever time you feel relevant. The data normally appear an hour or two after 00Z.

7. Modify whatever you feel like. 

8. Enjoy!






