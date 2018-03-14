
# COMPSCI 677 Distributed and Operating Systems : Spring 2017

# Programming Assignment 2: Asterix and the Olympic Games (Summer Games edition)

Due: 11:55pm, Friday March 30

    You may work in groups of two for this lab assignment.

    This project has two purposes: first to familiarize you with problems such as clock syncronization, logical clocks/event ordering, and multi-tier architectures.

    The programming assignment should be completed using Python. Where possible, you should build on the code that you wrote for the previous lab. You have considerable flexibility to make appropriate design decisions and implement them in your program.

A: The problem

    After the tremendous success of the winter Olympic games, the Gauls are preparing for the summer Olympic games. The summer games are expected to be singificantly more popular and draw more traffic than the winter games.
    Part 1: Multi-tier Web architecture and Replicated Servers
    To handle the surge in the number of smart stones accessing sports information, Obelix has decided to replicate the Stone server. Assume that there are now at least two stone servers that maintain sports scores. A tablet can request a score from either server. Further, motivated by the desire to use the best stone architecture known to humankind in 50BC, Obelix's stone server now employs a multi-tier architecture. This can simply be implemented by maintaining the database tier as a simple file on disk that stores the score and a database tier process that answers for read or write requests to data from the two (or more) front end servers. Thus the stone server has at least three processes: two front-end server processes that receive client requests and one backend datbase process that receives read or write requests from the front-end servers. Do not use an actual database to implement your database tier since we expect you to implement persistant database storage yourself. You can use any record format in your database file. Comma separated values (CSV) format is one example format that may be used. The schema for your database file should be documented in your design doc.

    Assume that the front end servers not only receive requests for scores but one of them also receives score updates from the Cacofonix process and then sends an update to the database tier.

    You only need to implement client-pull for this lab. Server push funcitonality is not needed. Further, while the API exposed by front-end servers is identical to lab 1, you should implement your own internal interface to handle interactions between the front-end and back-end processes (you can deisgn it any way you wish and this interface should be documented in your README file). Please use the same REST web API for the front end servers that was used in Lab 1.

    Load balancing across web servers: Since the front end server is replicated, you need to implement a load balancing mechanism to ensure that clients are load balanced across the two front-end tiers. This could be done in one of many ways. For example, the server could maintain a dispatcher process that keeps track of the number of clients assigned to each front end server. A new client can query the dispatcher and it can point the client to one of the two front-end servers based on the current load. The dispatcher should also update the load, which in this case is the number of clients assigned to each front end server, based on this assignment. Other more complex scenarios are allowed if you wish to be more creative with this part.
    Part 2: Leader election and clock synchronization
    Assume that the two front-end processes and the backend process run a leader election algorithm to elect a time server. You can use any leader election algorithm discussed in class for this purpose. Once a leader has been elected, this node also acts as a time server. Implement the Berkeley clock syncronization algorithm to syncromnize their clocks. Each node then maintains a clock-offset variable that is the amount of time by which the clock must be adjusted, as per the Berkeley algorithm. We will not actually adjust the system clock by this value. Rather to timestamp any request, we simply read the current system time, add this offset to the time, and use this adjusted time to timestamp request. Each incoming sports score update is now time-stamped with the syncronized clock value; this time stamp is included with each request for score so that villagers know when the score was last updated.
    Part 3: Event ordering using logical Clocks and totally ordered multicast
    As the official sponsor of the Olympic games, Rotten Apples Company is running a raffle for each villager who use their smart iStone tablets to acccess sports scores. The grand prize is a hunting trip for boars with Asterix, followed by an invitation to the grand feast for the gold medal winners that will be organized by chief Vitalstatistix.

    Every 100th request to the stone server is automatically entered into the raffle. However requests arrive concurrently to the two front-end servers, the stone server needs to be able to derive a total ordering of all incoming requests to flag every hundredth request. The Gauls are sticklers are precise synchronization and are unwilling to accept the error tolerence provided by the Berkeley algorithm in Part 2. Also atomic clocks are yet to be invented.

    To address this issue, we will use totally ordered multicasting using Logical clocks. The two front end servers will maintain a logical clock that be incremented upon the receiving each client request. As in totally ordered multicast, each request is buffered. The arrival of each client request is multicast to other front end replicas and logical clocks and totally ordered multicast protocol is used to derive a total ordering of all incoming requests. Every hundredth request in this total order is then chosen for the raffle entry.

    Please note that end-clients do not need to implement logical clocks. They are internal to the front-end servers. Please refer to class lecture slides and the replicated banking example for totally ordered multicasting in sec 6.2 of the textbook to understand how to implement this part.

    Again, every hundredth request is entered into a raffle. At the end, randomly choose a winner from all raffle entties.

    Like before assume that there are N tablets, each of which is a client, that needs to be periodically updated with sports scores. (N should be configurable in your system).

    Like before, Cacofonix, the village bard, is responsible for providing Obelix's server live updates from the olympic stadium, which he does by singing the scores and thereby sending updated scores to one of the front-end servers.
    Requirements:
        You need to implement all three parts. If possible, make separate directories for each part such as "multitier", "clocksync" and "raffle" in your source directory and maintain code for each part in these directories. This will simplify grading of each part of the lab.
        All the requirements of Project 1 still apply to Project 2, except that you no longer need to support server push in this part. 
    Other requirements:

        No GUIs are required. Simple command line interfaces and textual output of scores and medal tallies are fine.

        You are free to develop your solution on any platform, but please ensure that your programs run on the edlab machines (See note below). Please speccify whether your are using Python 2 or Python 3 in your design doc. 

B. Testing, Evaluation and Measurement

    Write a set of test cases to test each part of the lab. While the Gauls may be convinced that your code works well, use the test cases to convince yourself and, more importantly, the TAs that you have tested various scenarios and that your code works well. All tests should be documented and placed in the test directory.
    Compute the average response time of your new server as before. How does this multi-tier server compare to your previous lab? How much latency did the multi-tiering add?
    Design a experiment to show whether the workload is balanced among the two front end servers. Can your solution scale to three or more server? Either give a textual explanation as to why or, even better, run your code with three front end servers and show that the load balancing works.
    Design an experiment to show your totally-ordered multicasting, clock syncronization algorithm really do the work as you expect.

    Make necessary plots to support your conclusions.

C. What you will submit
When you have finished implementing the complete assignment as described above, you will submit your solution in github. Do not treat gihub as a final submission site where you only submit the final submission. You must use github for code development throughout the lab. Check in your code, test cases, documentation regularly as you work on the lab. We will look at your check-in history, number of commits, comments on your commits, etc., and assign points for proper use of github (see grading policy below).
Each program must work correctly and be documented. The final submission on githiub should contain:

    A README file listing the names of students in your group (do not include student IDs) as well as how to run your code. If we can't run it, we can't grade it. The REAMDE file should be a simple "user manual" of how to setup and run your code on the ed-lab.
    source code in the src directory for all three parts, with in-line comments.
    An electronic copy of the output generated by running your program. Print informative messages when a client or server receives and sends key messages and the scores/medal tallies.
    A seperate design document of approximately three pages describing the overall program design, a description of "how it works", and design tradeoffs considered and made. Be sure to document the design of EACH part separately. Also describe possible improvements and extensions to your program (and sketch how they might be made).
    A seperate description of the tests you ran on your program to convince yourself that it is indeed correct. Also describe any cases for which your program is known not to work correctly.
    Performance results.

D. Grading policy for all programming assignments

    Program Listing
        works correctly ------------- 60% (20% for each of the three parts)
        in-line comments / documentation -------- 5% 
    Design Document
        quality of design doc, through description and understandability ------------ 10%
        Creativity of your program design --------- 10% 
    Use of github with checkin comments --- 5%
    Thoroughness of test cases ---------- 10%
    Grades for late programs will be lowered 12 points per day late.

Note about edlab machines
We expect that most of you will work on this lab on your own machine or a machine to which you have access. However we will grade your submission by running it on the EdLab machines, so please keep the following instructions in mind.
Although it is not required that you develop your code on the edlab machines, we will run and test your solutions on the edlab machines. Testing your code on the edlab machines is a good way to ensure that we can run and grade your code. Remember, if we can't run it, we can't grade it.
There are no visiting hours for the edlab. You should all have remote access to the edlab machines. Please make sure you are able to log into and access your edlab accounts.
IMPORTANT - No submissions are to be made on edlab. Submit your solutions only via github.
Stumped?

    Who are the Gauls? Read about them on Wikipedia.
    Stumped on how to proceed? Review the comic book Asterix at the Olympic Games from your local library. Better yet, ask the TA or the instructor by posting a question on the Piazza 677 questions. General clarifications are best posted on Piazza. Questions of a personal nature regarding this lab should be asked in person or via email. 
