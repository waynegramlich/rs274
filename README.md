# `RS274` Python Module

In this document, the pronoun "we" is used to mean the `rs274` module developers
and "you* is used to mean you the reader.

## Some History

RS-274 is the overarching specification for "G-Codes" used by CNC machines.
The base RS-274 documents stretch back in time (EIA RS-274-C, NBSIR 76-1094, ...)

What has happened over time is that variants of RS-274 have been standardized
for different industrial segments.  Some examples are listed below:

* RS-274X:
  This format started as a CNC file for driving a Gerber photo-plotter that would expose film
  for making photo-tools for making Printed Circuit  boards.  It was extended to include
  something called aperture shapes which are the moral equivalent to tools on CNC milling
  machines.   The [Wikipedia Gerber File](https://en.wikipedia.org/wiki/Gerber_format)
  article gives an excellent overview of this RS-274 variant.

* Excellon Drill Format:
  This format is named after Excellon Automation Company which made CNC drilling machines
  for manufacturing printed circuit boards.  Again, the
  [Wikipedia Excellon format](https://en.wikipedia.org/wiki/Excellon_format)
  article is an excellent introduction to this variant.  Basically, it adds a
  drill tool table at the front of the file.

* CNC Machine Formats:
  The CNC machine industry standardized on the basics of RS-274, and then added
  various extensions that were particular to their products.  The newest version
  of the RS-274-D which was done by the NIST (National Institute of Standards and
  Technology.)  RS-274D is implemented by the LinuxCNC project.  While almost all
  CNC machine controllers will consume basic RS-274, they all have their quirks.
  CAM (Computer Aid Manufacture) software deals with these quirks with "post processors"
  that generate G-code that is specific to each particular manufacturer variant.

There are numerous books that teach CNC programming.  One of the more commonly
used ones is the "CNC Programming Handbook" by Peter Smid.  This this book is now
in its third edition, the second edition was referenced extensively while working
out the issues of the `rs274` Python module.

Now that you have a brief history what has transpired with RS-274, we can start to
talk about the over all architecture of the RS274 Python module.

## Overall Architecture

The goal of RS274 Python module is to provide an integrated pre/post processor
support for RS274.  While this module is initially targeted towards supporting
the FreeCAD project, it could be adapted for other projects as well.

The overall concept is that there is an RS274 base class that is specialized
for each RS274 variant.  The basic concept is:

        import rs274

        class RS274LinuxCNC(rs274.RS274):
	    # ...
	    def __init__(self, ...):
		# Specialize for the LinuxCNC variant of RS274...

	    def pre_process(self, ...):
		# Preprocessor for LinuxCNC...
		
	    def post_process(self, ...):
		# Postprocessor for LinuxCNC...

In general, postprocessors tend to be easier to write than preprocessors.  The
reason for this is that some users write pretty sloppy G-code that works, but can
fool a simple preprocessor with some the RS-274 subtleties.  Let us go over some
of the issues:

* Blocks vs. Left-to-Right:
  A CNC file consists of a bunch of lines where each line contains some control
  codes and/or some comments.  In RS-274 terminology, a line is called a *block*.
  A block is processed indivisibly as whole.  It is not processed left-to-right
  like reading a book.  Most simple preprocessors interpret the code left to right,
  and can generate incorrect command sequencing as a result.

  Let's start with the coolant M commands M7/M8/M9.  M7 turns on mist cooling,
  M8 turns on flood cooling, and M9 turns which ever one is on.  It is an error
  to attempt to turn on both at the same time.  The following lines of code:

	G0 X0 Y0 Z.5         (Rapid to the start location)
        M8 G1 Z-.5 F5000     (Turn on flood coolant, drive mill into material)
	G1 X5                (Mill a channel 5 units long in the +X direction)
	M9 G1 Z.5            (Retract mill bit and turn off coolant)

  For the last command, the G1 is actually executed first and then the M9
  is executed to turn off the coolant.  For a left to right execution, the
  coolant would be turned off before the final G1 command is executed.

  The reality of a G-code block is that *order does not matter*.  Yes, this is
  really a mind blowing concept, but the requirement of block indivisibility makes
  this the case.  If you reverse all the arguments, you still get the same result:

	Z.5 Y0 X0 G0         (Rapid to the start location)
        F5000 Z-.5 F1 M8     (Turn on flood coolant, feed into the mill at 5000 units/sec)
	X5 G1                (Mill a channel 5 units long in the +X direction)
	Z.5 M9 G1            (Retract mill bit and turn off coolant)

  The code immediately above is really quite ugly (hint do not write code like
  this), but it performs the same as the chunk immediately beforehand.

* S, F, and T are full commands:
  The next subtle issue is that S, F, and T are actual commands, just like G and M.
  What this means is that they can sit in a block all alone and they are completely
  valid.  For example,

        T10                  (Set tool number to 10; no tool change occurs)
        T11                  (Now set the tool number to 11; no tool change occurs)
	M6                   (Now change the tool to to 11)

  Likewise a spindle speed change command can occur anywhere in the block, but spindle speed
  change starts immediately.  Thus,

        S2500 G0 X0 Y0 Z0.5  (Start adjusting the spindle speed at the begining of the rapid)

  This is the same as:

        G0 X0 Y0 Z0.5 S2500  (Start adjusting the spindle speed at the begining of the rapid)

  The same thing occurs with the F command for changing feed rate:

        F2500 G1 X0 Y0 Z-.5  (Perform a material plunge at 2500 units/sec.)

  Again, this is the same as:

        G1 X0 Y0 Z-.5 F2400  (Perform a material plunge at 2500 units/sec.)
	
## How `RS274` Python module works:

For the preprocessor, the steps that occur are:

1. The block (i.e. line) is broken into individual tokens.  In general, each token
   is simply a letter followed by number.  There can be whitespace between tokens
   to improve legibility.

2. The tokens are broken into command tokens and parameter tokens based on letters.
   Command tokens start with one of the letter is 'FGMNST' and parameter commands
   are one of the remaining chacters in 'ABCDE..HIJKL..OPQR..UVWXYZ'.
   The command tokens are stored into a Python list and the parameter tokens
   are stored into Python dictonary.  Any duplicate parameter tokens are
   flagged as an error.

3. The command tokens are sorted into a sensible order.  Checks are made to ensure
   that commands that are incompatible with one another get flagged as an error.
   For example, a block can only have one spindle motion command per block
   (e.g G0, G1, G2, G3, and all canned cycles like G81, G82, ...)

4. The sorted command tokens are processed from left to right.  Any commands
   that need non-command tokens fetch them from the Python dictionary.  Some
   parameters are modal, some are required, and some are optional.  The modal
   ones are axes like A/B/C/I/J/K/U/V/W/X/Y/Z.

5. The final output is a sequence of commands with appropriate parameters.
   Is provided as Python list of (command_token, parameter_dictionary) tuple pairs.
   For example `[("G2", {'X':1.0, 'Y':2.0), ("M9", {})] corresponds to:

        G2 X1.0 Y2.0
	M9

6. For FreeCAD this output can trivially be turned into FreeCAD `Command`
   objects for insertion into a FreeCAD `Path` object.

All of the magic of this system occurs in step 4 above, where the sorting occurs.
So the order of sorting is basically as follows:

Unmodal:
G4: Dwell
G9: Path control mode, Exact Stop (pg. 88) not really supportable by FreeCAD,
    must be done with G61/G64 instead.



* G20/G21: (Distance Mode)
  These change units that are present in parameters between metric and imperial.

* G90/G90: These toggle incremental vs. absolute distances for the axes.

2. M0/M1

3. M6:

4. T: Combines with previous M6 when present

?. G43/G44 Tool Length Offset

?. G6

?. G41/G42: Cutter Radius Compensation.

5. M3/M4:

6. S: Combines with previous M3/M4 if present.

7. M7/M8:

?. G93/G94/G95: Feed rate mode: This changes the units of F.

8. G98/G99: Canned Cycle Return Mode

9. G17/G18/G19: (Plane Selection):

?. G0/G1/G2/G5.x/G81/G73/G76/G82/G83/G84/G85/G89: (Spindle Motion) These are the motion commands.a

?. F: Combines with preceding motion command when present.

?. G80

?. G99/G99

?. G49: Cancel Tool Length Compensation.

?. G4: Dwell

?. M9: Coolant off

?. M0/M1/M2/M30/M60: Various pause and stoppage commands.

The way this list is constructed is by inserting before, after, or at command
that is already present.

