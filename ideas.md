# Ideas

## Hand recognition
Requirements/flow
- Camera is positioned above hand
- User moves fingers as if playing a keyboard
- Their fingers are mapped to imaginary/virtual "keys", and when pressed, these keys will map to real physical keyboard keys via servo motors
- Specifics
    - Depending on the distance of the hand, the virtual keys will shrink
- Recognition model outputs *the set of pressed coordinates* (there are up to 5 of these due to 1 hand)

## Playing keys
- State: *set of pressed keys*
- Each frame, compare current state to previous frame's state
    - Map each set of pressed coordinates to the set of pressed keys based on space/distance
    - When a key has just gone down, update Arduino
        - *lift up all other servos* and *put down the servo for the key that was pressed*

## Technical
- Do as much as possible in Python on the Linux side, then send necessary information to the Arduino side
