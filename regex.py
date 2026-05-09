from __future__ import annotations
from abc import ABC, abstractmethod
import argparse
import sys
class State(ABC):
    @abstractmethod
    def __init__(self) -> None:
        pass

    @abstractmethod
    def check_self(self, char: str) -> bool:
        """
        Checks whether the given character is accepted by this state.
        """
        pass

    def check_next(self, next_char: str) -> State:
        for state in self.next_states:
            if state.check_self(next_char):
                return state
        raise NotImplementedError("rejected string")


class StartState(State):
    def __init__(self):
        self.next_states: list[State] = []

    def check_self(self, char: str) -> bool:
        return False


class TerminationState(State):
    def __init__(self):
        self.next_states: list[State] = []

    def check_self(self, char: str) -> bool:
        return False


class DotState(State):
    """State for '.' — accepts any character."""

    def __init__(self):
        self.next_states: list[State] = []

    def check_self(self, char: str) -> bool:
        return True


class AsciiState(State):
    """State for a specific ASCII letter or digit."""

    def __init__(self, symbol: str) -> None:
        self.curr_sym = symbol
        self.next_states: list[State] = []

    def check_self(self, curr_char: str) -> bool:
        return curr_char == self.curr_sym


class StarState(State):
    """
    State for the '*' quantifier (zero or more).
    """

    def __init__(self, checking_state: State):
        self.checking_state = checking_state
        self.next_states: list[State] = []

    def check_self(self, char: str) -> bool:
        return self.checking_state.check_self(char)

    def check_next(self, next_char: str) -> State:

        for state in self.next_states:
            if state is not self and state.check_self(next_char):
                return state

        if self.check_self(next_char):
            return self
        raise NotImplementedError("rejected string")


class PlusState(State):
    """
    State for the '+' quantifier (one or more).
    """

    def __init__(self, checking_state: State):
        self.checking_state = checking_state
        self.next_states: list[State] = []

    def check_self(self, char: str) -> bool:
        return self.checking_state.check_self(char)

    def check_next(self, next_char: str) -> State:
        for state in self.next_states:
            if state is not self and state.check_self(next_char):
                return state
        if self.check_self(next_char):
            return self
        raise NotImplementedError("rejected string")


class RegexFSM:
    """
    Compiles a regex pattern into a linked chain of State objects and
    uses that chain to accept or reject input strings.

    """

    def __init__(self, regex_expr: str) -> None:
        self.curr_state = StartState()

        frontier: list[State] = [self.curr_state]

        last_new: State | None = None
        last_new_parents: list[State] = []

        for char in regex_expr:
            new_state = self.__init_next_state(
                char, frontier, last_new, last_new_parents
            )
            if new_state is not None:
                last_new_parents = list(frontier)
                last_new = new_state
                for s in frontier:
                    s.next_states.append(new_state)
                frontier = [new_state]

        term = TerminationState()
        for s in frontier:
            s.next_states.append(term)

    def __init_next_state(
        self,
        next_token: str,
        frontier: list[State],
        last_new: State | None,
        last_new_parents: list[State],
    ) -> State | None:

        match next_token:
            case ".":
                return DotState()

            case "*":

                star = StarState(last_new)
                for parent in last_new_parents:
                    if last_new in parent.next_states:
                        parent.next_states.remove(last_new)
                        parent.next_states.append(star)

                frontier.clear()
                frontier.extend(last_new_parents)
                frontier.append(star)
                return None

            case "+":

                plus = PlusState(last_new)
                for parent in last_new_parents:
                    if last_new in parent.next_states:
                        parent.next_states.remove(last_new)
                        parent.next_states.append(plus)
                frontier.clear()
                frontier.append(plus)
                return None

            case _ if next_token.isascii() and (
                next_token.isalpha() or next_token.isdigit()
                ):
                return AsciiState(next_token)

            case _:
                raise AttributeError(f"Character '{next_token}' is not supported")

    def check_string(self, input_string: str) -> bool:
        """
        Returns True if *input_string* is fully matched by the compiled regex.
        """
        current_state: State = self.curr_state
        for char in input_string:
            try:
                current_state = current_state.check_next(char)
            except NotImplementedError:
                return False

        return isinstance(current_state, TerminationState) or any(
            isinstance(s, TerminationState) for s in current_state.next_states)
def main() -> None:

    parser = argparse.ArgumentParser(description="Simple Regex Matcher")
    parser.add_argument("pattern", help="Regex pattern")
    parser.add_argument("strings", nargs="+", help="Strings to test")

    args = parser.parse_args()

    try:
        fsm = RegexFSM(args.pattern)
    except AttributeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    for s in args.strings:
        result = fsm.check_string(s)
        print(result)

if __name__ == "__main__":
    main()
