# sharesfor
---
sharesfor is an open source messaging and collaboration platform, that features simple integration capabilities with your existing applications. 
sharesfor can relate to objects in your existing application and provide message threads related to that object -and others that may be co-related- thereby sharing and collecting information on it.

Objects can for instance be the accounts, contacts, projects, etc. in your CRM; the courses, lectures, subjects, classes, etc. on your Learning Management Sytem;  or any other item in any of your applications.

sharesfor provides a familiar real time messaging interface so that users provide personal/corporate memory on those objects by creating and populating message threads. It provides a real time messaging mechanism, so users can chat on the objects while creating valuable information for their organization, company, community, etc. A simple demo is available  [here](https://s4s4demo.pluralist.team) which presents some sample objects that link to sharesfor where you can create and append to message threads on them. 

sharesfor provides two interfaces and a common my messages pop-up
The primary interface lists the shares (threads) that are related to the object for which sharesfor is activated
![main object page](https://github.com/ceskinat/sharesfor/blob/main/assets/screenshots/objmain.png)

When a thread is clicked a thread detail interface is activated. From here you can view all the messages and shares in that thread, as well as add new mesages/notes to this thread
![thread detail](https://github.com/ceskinat/sharesfor/blob/main/assets/screenshots/thrdetail.png)

From any of these interfaces, you can activate the "My Messages" pop-up which lists the shares you are in the audience list
![My Messages](https://github.com/ceskinat/sharesfor/blob/main/assets/screenshots/mymsgs.png)

sharesfor is activated through a POST request with the following parameters:
{userid, username, email, otype, oid}
which corresponds to user information (userid, username, email) and object information (otype: object type; oid: object id). 

See integration.md for integrating your application with sharesfor and installation.md for sharesfor installation instructions.


### Technology Stack
-- Backend: Python Flask
-- Database: MongoDB
-- Real-Time Communication: Socket.IO


### Contributing
Contributions are welcome! To contribute:
	Fork the repository.
	Create a new branch for your feature or bug fix.
	Submit a pull request.

### License
This project is licensed under the MIT License. See the LICENSE file for details.

### Contact

For questions or support, please reach out to:

Email: ceskinat@gmail.com



