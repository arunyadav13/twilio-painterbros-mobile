import React from "react";
import ParticipantDetails from "./ParticipantDetails";

class PrimaryParticipant extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    const {
      callElement,
      participantElement,
      participants,
      conn,
      removeParticipant,
      toggleDisplayPrimaryActionButton,
      conferenceStatus,
      callDetails,
      alterDisplayIndividualCallDetails,
      user,
      alterButtonDiableProperty
    } = this.props;
    return (
      <div className="primaryParticipant">
        <ParticipantDetails
          participantElement={participantElement}
          participants={participants}
          conn={conn}
          callElement={callElement}
          removeParticipant={removeParticipant}
          toggleDisplayPrimaryActionButton={toggleDisplayPrimaryActionButton}
          conferenceStatus={conferenceStatus}
          callDetails={callDetails}
          alterDisplayIndividualCallDetails={alterDisplayIndividualCallDetails}
          user={user}
          alterButtonDiableProperty={alterButtonDiableProperty}
        />
      </div>
    );
  }
}

export default PrimaryParticipant;
