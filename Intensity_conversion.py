
import streamlit as st
import pandas as pd
import numpy as np

# --------------------------------------------------
# Constants
# --------------------------------------------------
H = 6.62607015e-34
C = 299792458
NA = 6.02214076e23
K_M = 683.0

st.set_page_config(
    page_title="Optical Unit Converter",
    page_icon="💡",
    layout="centered",
)

UNITS = [
    "μmol m⁻² s⁻¹",
    "W",
    "mW",
    "cd",
]

# Approximate CIE 1931 photopic luminous efficiency V(lambda).
CIE_VALUES = {
    380: 0.000039, 390: 0.000120, 400: 0.000396,
    410: 0.001210, 420: 0.004000, 430: 0.011600,
    440: 0.023000, 450: 0.038000, 460: 0.060000,
    470: 0.091000, 480: 0.139020, 490: 0.208020,
    500: 0.323000, 510: 0.503000, 520: 0.710000,
    530: 0.862000, 540: 0.954000, 550: 0.995000,
    560: 0.995000, 570: 0.952000, 580: 0.870000,
    590: 0.757000, 600: 0.631000, 610: 0.503000,
    620: 0.381000, 630: 0.265000, 640: 0.175000,
    650: 0.107000, 660: 0.061000, 670: 0.032000,
    680: 0.017000, 690: 0.008210, 700: 0.004102,
    710: 0.002091, 720: 0.001047, 730: 0.000520,
    740: 0.000249, 750: 0.000120, 760: 0.000060,
    770: 0.000030, 780: 0.000015,
}


def photopic_efficiency(wavelength_nm):
    """Interpolate the approximate CIE V(lambda) table."""
    wavelengths = np.array(list(CIE_VALUES.keys()), dtype=float)
    efficiencies = np.array(list(CIE_VALUES.values()), dtype=float)

    if not 380 <= wavelength_nm <= 780:
        raise ValueError(
            "Supported wavelengths are 380–780 nm."
        )

    return float(np.interp(
        wavelength_nm, wavelengths, efficiencies
    ))


def calculate_conversions(
    value,
    input_unit,
    output_units,
    wavelength_nm=None,
    area_m2=None,
    solid_angle_sr=None,
):
    """Convert between photon flux density, W, mW and cd."""

    if value < 0:
        raise ValueError("Input value must be non-negative.")

    # Wavelength is only needed for photon or candela conversions.
    needs_wavelength = (
        input_unit in ("μmol m⁻² s⁻¹", "cd")
        or any(u in ("μmol m⁻² s⁻¹", "cd") for u in output_units)
    )

    if needs_wavelength and wavelength_nm is None:
        raise ValueError("Wavelength is required.")

    if wavelength_nm is not None and not 380 <= wavelength_nm <= 780:
        raise ValueError("Supported wavelengths are 380–780 nm.")

    needs_area = (
        input_unit == "μmol m⁻² s⁻¹"
        or "μmol m⁻² s⁻¹" in output_units
    )

    if needs_area and (area_m2 is None or area_m2 <= 0):
        raise ValueError("Area must be greater than zero.")

    needs_solid_angle = (
        input_unit == "cd" or "cd" in output_units
    )

    if needs_solid_angle and (
        solid_angle_sr is None or solid_angle_sr <= 0
    ):
        raise ValueError("Solid angle must be greater than zero.")

    # Convert input to radiant power (W).
    if input_unit == "W":
        power_w = value

    elif input_unit == "mW":
        power_w = value / 1000.0

    elif input_unit == "cd":
        v_lambda = photopic_efficiency(wavelength_nm)
        if v_lambda <= 0:
            raise ValueError("Photopic efficiency must be positive.")

        power_w = (
            value * solid_angle_sr / (K_M * v_lambda)
        )

    elif input_unit == "μmol m⁻² s⁻¹":
        energy_per_photon = (
            H * C / (wavelength_nm * 1e-9)
        )
        photon_rate_mol_s = value * area_m2
        power_w = (
            photon_rate_mol_s * 1e-6
            * NA * energy_per_photon
        )

    else:
        raise ValueError("Unsupported input unit.")

    results = {}
    energy_per_photon = (
        H * C / (wavelength_nm * 1e-9)
        if needs_wavelength else None
    )

    for unit in output_units:
        if unit == "W":
            results[unit] = power_w

        elif unit == "mW":
            results[unit] = power_w * 1000.0

        elif unit == "cd":
            v_lambda = photopic_efficiency(wavelength_nm)
            results[unit] = (
                K_M * v_lambda * power_w / solid_angle_sr
            )

        elif unit == "μmol m⁻² s⁻¹":
            photon_rate_mol_s = (
                power_w / energy_per_photon / NA
            )
            results[unit] = (
                photon_rate_mol_s * 1e6 / area_m2
            )

    return results

# --------------------------------------------------
# User interface
# --------------------------------------------------
st.title("💡 Optical Unit Converter")

st.write(
    "Convert photon flux density (PAR), radiant power, and "
    "luminous intensity for monochromatic light."
)

st.info(
    "Select one input unit and one or more output units. "
)

with st.form("conversion_form"):
    input_unit = st.selectbox("Convert from", UNITS)

    output_units = st.multiselect(
        "Convert to",
        [u for u in UNITS if u != input_unit],
        default=[u for u in UNITS if u != input_unit],
    )

    value = st.number_input(
        f"Input value ({input_unit})",
        min_value=0.0,
        value=1.0,
        format="%.8g",
    )

    needs_photon = (
        input_unit == "μmol m⁻² s⁻¹"
        or "μmol m⁻² s⁻¹" in output_units
    )
    needs_candela = input_unit == "cd" or "cd" in output_units

    # Wavelength is required for photon and candela conversions.
    needs_wavelength = needs_photon or needs_candela

    if needs_wavelength:
        wavelength_nm = st.number_input(
            "Wavelength (nm)",
            min_value=380.0,
            max_value=780.0,
            value=555.0,
            step=1.0,
            help="The photopic model supports 380–780 nm.",
        )
    else:
        wavelength_nm = None

    if needs_photon:
        area_m2 = st.number_input(
            "Illuminated area (m²)",
            min_value=0.000001,
            value=1.0,
            format="%.8g",
            help="Required to convert total photon rate and photon flux density.",
        )
    else:
        area_m2 = None

    if needs_candela:
        solid_angle_sr = st.number_input(
            "Emission solid angle (sr)",
            min_value=0.000001,
            max_value=12.566371,
            value=1.0,
            format="%.6f",
            help="Effective emission solid angle; a full sphere is approximately 4π sr.",
        )
    else:
        solid_angle_sr = None

    submitted = st.form_submit_button(
        "Convert",
        type="primary",
        use_container_width=True,
    )

if submitted:
    if not output_units:
        st.warning("Select at least one output unit.")
    else:
        try:
            results = calculate_conversions(
                value=value,
                input_unit=input_unit,
                output_units=output_units,
                wavelength_nm=wavelength_nm,
                area_m2=area_m2,
                solid_angle_sr=solid_angle_sr,
            )

            st.subheader("Conversion results")

            df = pd.DataFrame({
                "Output unit": list(results.keys()),
                "Converted value": [
                    f"{result:.8g}"
                    for result in results.values()
                ],
            })

            st.dataframe(
                df,
                hide_index=True,
                use_container_width=True,
            )

            if needs_wavelength:
                st.caption(
                    f"Wavelength: {wavelength_nm:g} nm"
                    + (
                        f" | V(λ): "
                        f"{photopic_efficiency(wavelength_nm):.6g}"
                        if needs_candela else ""
                    )
                )

        except ValueError as error:
            st.error(str(error))

st.divider()

st.caption(
    "Note: Candela is a photometric quantity. Its conversion "
    "depends on wavelength, the photopic response model, "
    "and the assumed emission solid angle. Photon flux density "
    "is expressed in µmol/s/m²."
)
