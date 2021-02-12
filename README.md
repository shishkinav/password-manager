# saverpwd

### Password manager with a command-line interface

saverpwd is a multi-user, multi-platform command-line utility for storing and organizing passwords and another info for
logins

### Contents
1\. Common commands

2\. Installing the utility

3\. Backup and restore data
<br>
<br>

1. Common commands
   <br>
   <br>

   help on using the utility:
   ```
   $ saverpwd --help
   ```
   <br>   

   more detailed help on using utility commands:
   ```
   $ saverpwd [command] --help
   ```
   <br>   

   adding a new user:
   ```
   $ saverpwd uadd
   ```
   or using options:
   ```
   $ saverpwd uadd -u user-name
   ``` 
   <br>      

   adding a new record in passwords DB:
   ```
   $ saverpwd add
   ```
   or using options:
   ```
   $ saverpwd add -u user-name -l login-for-site -n record-name
   ```
   <br>   

   show all user records:
   ```
   $ saverpwd show
   ```
   <br>   

   get the password of record to the clipboard:
   ```
   $ saverpwd get
   ```
   or using options:
   ```
   $ saverpwd get -n record-name
   ```
   <br>   

   full list of command options:
   ```
   $ saverpwd [command] --help
   ```
   <br>  

2. Installing the utility

   <br>

    1. Installing on Ubuntu
       <br>   
       the utility requires python 3.8 or higher

       check version python:
       ```
       $ python3 --version
       ```
       <br>
       install pip3:
       
       ```
       $ sudo apt update
       $ sudo apt upgrade
       $ sudo apt install python3-pip
       $ pip3 --version
       ```
       <br>
       install pipenv:
       
       ```
       pip3 install --user pipenv
       ```
       if you see a warning like this
       ```
       WARNING: The script virtualenv is installed 
       in '/home/user-name/.local/bin' which is not on PATH.
       ```
       follow this:
         - Open ~/.profile file.
         - Check if ~/.local/bin path exists in that file.
         - If not add these following lines:
            ```
            # set PATH so it includes user's private bin if it exists
            if [ -d "$HOME/.local/bin" ] ; then
               PATH="$HOME/.local/bin:$PATH"
            ```
         - Run bash --login for login mode because ~/.profile 
           is executed for login shells.
           <br>
    <br>      

    install saverpwd:
    ```
    $ cd saverpwd-folder
    $ pipenv install -e .
    $ pipenv shell
    ```
    <br>                 

    2. Installing on Windows
   
   <br>
   
   the utility requires python 3.8 or higher<br> 
   check version python:
   ```
   $ python --version
   ```
   
   check pip3:
   ```
   $ pip3 --version
   ```
   install pipenv:
   
   ```
   pip3 install pipenv
   ```    

   install saverpwd:
   ```
   $ cd saverpwd-folder
   $ pipenv install -e .
   $ pipenv shell
   ```   

   making .msi installer for Windows:
   ```
   $ python setup.py bdist --format=msi
   ```   

   run the .msi installer in the 'dist' folder by double click
   <br>
   <br>
   To uninstall saverpwd, look in Apps & features Windows 
   for an application like 'Python saverpwd-1.0'
   

3. Backup and restore data
   <br>
   <br>
   All data is stored in the database.sqlite file. 
   You can simply copy the database.sqlite file for 
   backup and replace the database.sqlite file with 
   the one you previously saved to restore all data.