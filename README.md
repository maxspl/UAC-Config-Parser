# UAC (Unix-like Artifacts Collector) configuration parser

Tool made to have a clear view of the configurations of UAC : what is collected, how it is collected.

![Alt text](/assets/Result.png)

## Usage
The tool can work on both linux and windows.

It takes only on argument which is the path of the UAC repository.
```
python UAC-Config-Parser.py <path of UAC>
```

## Usage example

Clone the original UAC repo
```
cd example
git clone https://github.com/tclahr/uac.git
```
![Alt text](/assets/UAC_cloned.png)

Run the tool
```
python ..\UAC-Config-Parser.py "C:\Users\maxspl\UAC-Config-Parser\example\uac"
```
![Alt text](/assets/Exec_example.png)

## Result
![Alt text](/assets/Result1.png)
![Alt text](/assets/Result2.png)


A csv file should appear in the current dir.

