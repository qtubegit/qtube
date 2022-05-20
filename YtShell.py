import subprocess

class YtShell:
    def pipeOutput(command):
        pipe = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = pipe.stdout.read()
        out = out.decode('utf8')
        err = pipe.stderr.read()
        err = err.decode('utf8')
        return out, err
