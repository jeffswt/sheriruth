
# sheriruth

> It's difficult to describe that sensation which overwhelms her now. A riptide of glass that doesn't shatter, cut, or reflect her face, pushing past her in powerful amounts, turning up and swirling as if pulled by a great wind. She stands fast, and watches. Watches... memories.. of a filthy world. "What is this...!? She reaches out. "This.. " A memory of pain, betrayal, envy. When she stops it, she stops the rest. They stand still in the air around her, frozen. She whips her head this way and that. "They're only. Dark? Are they only dark? Wherever it is these -shards reflect. she sees little light there. Whatever small sparks she sees fade away in an instant. She bites her lip, and then smiles a smile with no humor. "What kind of joke is that?" she mutters, "A world filed only with misery.. As she says this, even her bitter smile fades away.

Fully Automatic Previous-Generation RUC Course Selector.

![Grimoire of Darkness](./assets/cover.jpg)

<del>While in reality I am a noob can't play Arcaea (try Fracture Ray</del>

<del>All Arcaea beatmaps on osu! are entirely c**p, how on earth are these beatmaps ranked (</del>

<del>Still no taiko Arcaea beatmaps -- even if they get ranked they are still Inner Oni ones -- and don't even try HR (</del>

## Installation

Python 3 and certain dependencies are required to run Sheriruth.

```bash
# Clone current repository
git clone https://github.com/[WhoeverItIs]/sheriruth.git
cd sheriruth
# Install dependencies
pip install -r requirements.txt
```

Or you may download pre-built binaries instead. You can find them on the *Releases* page (if there are any!).

## Usage

Sheriruth is, as it might look like, a command-line tool.

```bash
# Either:
python sheriruth.py [ARGS]
#  ^ If you have Python 2 on your system, make sure Python 3 is used in this case
# Or:
sheriruth.exe [ARGS]
#    ^ If you are using a pre-built Windows binary
```

Username and password are to be stored in `token.json` or any filename you want, as long as its format does not vary.

```json
{
    "username": "...",
    "password": "...",
    ...,
    "select": [
    	"...",
    	"...",
    	...,
    ]
}
```

Command-line arguments can be learned from `-h` invoking help.

At this point, a database containing course information should be initialized, which can be done with `-r` or `--reload` argument.

Now you can enter the Course IDs (they should look like `2018123012034056`) into the `select` entry in file `token.json`.

Now you can start looking for courses and get them with `-s` or `--start` whenever you want!

## Behavior

Sheriruth will look for courses (under the `select` wishlist) that are not yet "out of order", and select them (nearly) instantly whenever possible.

Information are shown live in the log window.

## Liability

The author and maintainers hold no liability to the maintenance, behavior, stability, performance, robustness and potential consequences of this software, and strongly recommend users to keep a human backup behind this in terms of emergency situations. That is to say:

1. You should not expect this program to work (though it usually works).
2. You should not expect this program to work for too long (though it should work for a few hours, I think).
3. You should expect this program to crash at some moment (though it usually do not).
4. You should expect this program to be laggy and thirsty of resources (though it consumes little disk, memory and CPU resources)
5. You should expect this program to behave differ from what is said to have done, at certain rare occasions.
6. We are not to be blamed when you did not achieve satisfying results with this program.
7. We are not to be blamed when the program did something in the wrong way.
8. We are not to be blamed if you find this program hard to use.
9. We are not to be blamed if you suffered great loss (in any means) from using this program, either directly or indirectly.
10. **[MUST READ] Setting a low *Request Delay* or a high *Refresh Rate* (This can be done with command-line arguments) might result in a temporarily disabled account, a PERMANENTLY BANNED account or even PUNISHMENT to the user.**
11. **[MUST READ] Users are expected to inspect the page by themselves. This program does not guarantee 100% success of getting your favourite classes.**

## Known issues

* [ ] `Ctrl+C` does not terminate the program, sometimes.
* [ ] No *unselect* interfaces implemented.
* [ ] Author does not wish to continue development of this project.

## License

```
    Sheriruth  RUC Course Selector
    Copyright (C) 2019  jeffswt.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

That means you should publish the source code if you want to put it on a server (though I highly suspect anyone would try to do this).