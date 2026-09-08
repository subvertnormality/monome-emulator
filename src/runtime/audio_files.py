"""Snapshot explicitly selected media into an owned session, preserving originals."""
import hashlib
from pathlib import Path
from automation.protocol import ContractError

def import_files(directory,files,audio_directory=None):
    directory=Path(directory);sources=[(source,source.name) for source in [Path(p).resolve() for p in files]];directories=[]
    if audio_directory is not None:
        root=Path(audio_directory).resolve()
        if not root.is_dir():raise ContractError('audio_directory_missing','Audio directory is missing: '+str(root))
        for source in sorted(root.rglob('*')):
            relative=source.relative_to(root).as_posix()
            if source.is_symlink():raise ContractError('audio_directory_link','Audio directory contains a symlink: '+relative)
            if source.is_dir():directories.append(relative)
            elif source.is_file():sources.append((source,relative))
            else:raise ContractError('audio_directory_entry','Unsupported audio entry: '+relative)
    names=set()
    for relative in directories:
        target=directory/relative
        if target.exists() and not target.is_dir():raise ContractError('audio_file_exists','Audio directory conflicts with '+relative)
    for source,relative in sources:
        if not source.is_file():raise ContractError('audio_file_missing','Audio file is missing: '+str(source))
        if relative in names or (directory/relative).exists() or relative in directories:
            raise ContractError('audio_file_exists','Audio import would overwrite '+relative)
        names.add(relative)
    for relative in directories:(directory/relative).mkdir(parents=True,exist_ok=True)
    records=[]
    for source,relative in sources:
        digest=hashlib.sha256();size=0;target=directory/relative
        with source.open('rb') as original,target.open('xb') as copied:
            before=source.stat()
            while True:
                block=original.read(1024*1024)
                if not block:break
                copied.write(block);digest.update(block);size+=len(block)
            after=source.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
            raise ContractError('audio_file_changed','Audio source changed during import: '+str(source))
        records.append(dict(path=relative,source=str(source),size=size,sha256=digest.hexdigest()))
    return records
