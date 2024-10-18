*maintenance* feature gives user an overview on the
**databases**, **schemas**, **tables** or **indexes** respective **size**.

It's very useful to get information about **bloat** and **toast**.
This can help users determine potential issues and understand or prevent performance issues due to
unaccordingly used space.

The *maintenance* feature also provides easy access to administrative actions such as **VACUUM**,
**ANALYZE** or **REINDEX** in order to fix space or performances problems.


!!! note

    Please beware that the values for bloat, toast, etc… are estimated.
    They may not perfectly reflect the reality especially if there hasn't been
    any analyze performed recently.


## Views

The maintenance plugin lets you navigate through databases, schemas and tables
of the instance.

![Maintenance databases page](sc/maintenance_databases.png)

![Maintenance schema page](sc/maintenance_schemas.png)

The page for one table shows more detailed information.

![Maintenance table page](sc/maintenance_tables.png)

## Hints

Once in a while temBoard may be able to provide some hints on actions to
perform on tables or indexes.

![Maintenance hints](sc/maintenance_hints.png)


## Actions

If you're logged onto the agent, you may then be able to perform actions by
clicking on the dedicated buttons.

temBoard can let you launch different actions such as **ANALYZE**, **VACUUM** or
**REINDEX**

You can also choose either to launch the action immediately or in the future
at the date and time you decide.

![Maintenance VACUUM schedule](sc/maintenance_schedule_vacuum.png)
