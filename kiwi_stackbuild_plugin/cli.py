# Copyright (c) 2025 SUSE LLC.  All rights reserved.
#
# This file is part of kiwi-stackbuild.
#
# kiwi-stackbuild is free software: you can redistribute it and/or modify
# it under the terms owf the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi-stackbuild is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi-stackbuild.  If not, see <http://www.gnu.org/licenses/>
#
import typer
import itertools
from pathlib import Path
from typing import (
    Annotated, Optional, List, Union, no_type_check
)

typers = {
    'stackbuild': typer.Typer(
        add_completion=False
    ),
    'stash': typer.Typer(
        add_completion=False
    )
}

system_stackbuild = typers['stackbuild']
system_stash = typers['stash']


@no_type_check
@system_stackbuild.command(
    context_settings={
        'allow_extra_args': True,
        'ignore_unknown_options': True
    }
)
def kiwi(
    ctx: typer.Context
):
    """
    List of command parameters as supported by the kiwi-ng
    build or create command. The information given here is passed
    along to the kiwi-ng system build or the kiwi-ng system create
    command depending on the presence of the --description
    option.
    """
    Cli = ctx.obj
    args = ctx.args
    for option in list(set(args)):
        if type(option) is not str or not option.startswith('-'):
            continue
        k: List[Union[str, List]] = [option]
        v = []
        indexes = [n for n, x in enumerate(args) if x == option]
        if len(indexes) > 1:
            for index in indexes:
                v.append(args[index + 1])
            for index in sorted(indexes, reverse=True):
                del args[index + 1]
                del args[index]
            k.append(v)
            args += k
    Cli.subcommand_args['stackbuild']['system_build_or_create'] = \
        dict(itertools.zip_longest(*[iter(args)] * 2))
    Cli.global_args['command'] = 'stackbuild'
    Cli.global_args['system'] = True
    Cli.cli_ok = True


@system_stackbuild.callback(
    help='Build an image based on a given stash container root. '
    'If no KIWI --description parameter is provided, '
    'stackbuild rebuilds the image from the stash container. '
    'In this case, the given kiwi parameters are passed to the '
    'kiwi-ng system create command. If a KIWI description is '
    'provided, this description takes over precedence and a new '
    'image from this description based on the given stash container '
    'root will be built. In this case, the given kiwi parameters '
    'are passed to the kiwi-ng system build command.',
    invoke_without_command=False,
    subcommand_metavar='kiwi [OPTIONS]'
)
def stackbuild(
    ctx: typer.Context,
    stash: Annotated[
        List[str], typer.Option(
            help='<name> Name of the stash container. See system stash --list '
            'for available stashes. Multiple --stash options will be stacked '
            'together in the given order'
        )
    ],
    target_dir: Annotated[
        Path, typer.Option(
            help='<directory> The target directory to store the '
            'system image file(s)'
        )
    ],
    description: Annotated[
        Optional[Path], typer.Option(
            help='<directory> Path to KIWI image description'
        )
    ] = None,
    from_registry: Annotated[
        Optional[str], typer.Option(
            help='<URI> Pull given stash container name from the '
            'provided registry URI'
        )
    ] = None,
):
    Cli = ctx.obj
    Cli.subcommand_args['stackbuild'] = {
        '--stash': stash,
        '--target-dir': target_dir,
        '--description': description,
        '--from-registry': from_registry,
        'help': False
    }


@system_stash.callback(
    help='Create a container from the given root directory',
    invoke_without_command=True,
    subcommand_metavar=''
)
def stash(
    ctx: typer.Context,
    root: Annotated[
        Optional[Path], typer.Option(
            help='<directory> The path to the root directory, '
            'usually the result of a former system prepare or '
            'build call'
        )
    ] = None,
    tag: Annotated[
        Optional[str], typer.Option(
            help='<name> The tag name for the container. '
            'By default set to: latest'
        )
    ] = None,
    container_name: Annotated[
        Optional[str], typer.Option(
            help='<name> The name of the container. By default '
            'set to the image name of the stash'
        )
    ] = None,
    stash_list: Annotated[
        Optional[bool], typer.Option(
            '--list',
            help='List the available stashes'
        )
    ] = False
):
    Cli = ctx.obj
    Cli.subcommand_args['stash'] = {
        '--root': root,
        '--tag': tag,
        '--container-name': container_name,
        '--list': stash_list,
        'help': False
    }
    Cli.global_args['command'] = 'stash'
    Cli.global_args['system'] = True
    Cli.cli_ok = True
